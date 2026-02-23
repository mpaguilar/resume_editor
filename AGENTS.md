# Agent Guide: Resume Editor

## Project Overview

A web-based multi-user resume authoring, editing, and export application built with Python 3.12, FastAPI, and HTMX. Users can create resumes in Markdown format and leverage LLM assistance for refinement and export to DOCX.

## Key Dependencies

- **FastAPI**: Web framework with API routes
- **HTMX**: Dynamic frontend interactions
- **Tailwind CSS**: Styling
- **PostgreSQL**: Data storage with Alembic migrations
- **resume_writer**: External library for parsing and exporting (always assume available)

## Architecture Patterns

### Route Organization

**Main Structure:**
```
resume_editor/app/api/routes/
├── resume.py              # Main resume CRUD
├── resume_edit.py         # Structured editing (personal, education, experience, certs)
├── resume_ai.py           # AI refinement with SSE streaming
├── resume_export.py       # Markdown/DOCX export
├── user.py                # Authentication and settings
├── admin.py               # Admin user management
├── pages/setup.py         # Initial setup wizard
├── html_fragments.py      # HTML generation helpers
├── route_models.py        # Pydantic models and form classes
└── route_logic/           # Business logic modules
    ├── resume_crud.py
    ├── resume_ai_logic.py
    ├── resume_serialization.py
    ├── user_crud.py
    └── ...
```

**Key Pattern:** Routes delegate to `route_logic/` modules. Keep business logic out of route handlers.

### Database Access
- Use SQLAlchemy with dependency injection via `Depends(get_db)`
- Always use `Annotated[Session, Depends(get_db)]` pattern per FastAPI conventions
- Alembic migrations in standard location

### Frontend Approach
- HTMX for dynamic interactions, not React/Vue
- Server-Sent Events (SSE) for real-time progress updates (AI tasks)
- Templates in `resume_editor/app/templates/`
- Minimal JavaScript, maximum server-side rendering

## Critical Implementation Details

### resume_writer Module
- **Never** check if it exists - assume it's always available
- Raises `ImportError` on missing import
- Reference `resume_writer_docs.md` for API details
- `BasicBlockParse` is a dynamic base class (methods added at runtime)

### LLM Integration
- All LLM calls **must** use `PydanticOutputParser`
- Include `format_instructions` in all LLM messages
- Parse responses with `langchain_core.utils.json.parse_json_markdown`
- API key from `LLM_API_KEY` environment variable
- Support custom OpenAI-compatible endpoints

### Authentication & Security
- Role-based: `user` and `admin`
- Encrypted storage for API keys and sensitive settings
- Middleware enforces initial setup if no users exist
- Password change workflow can be mandatory
- User impersonation available for admins

### Resume Data Flow
1. User creates/edits via HTMX forms
2. Stored as Markdown in PostgreSQL
3. Parsed using `resume_writer` for validation
4. LLM refinement happens on structured sections
5. Export to Markdown or DOCX (ATS_FRIENDLY, PLAIN formats)

## HTMX Patterns

### Content Negotiation
All routes that serve both HTMX and API clients must check the `HX-Request` header:
```python
if "HX-Request" in http_request.headers:
    # Return HTML fragment or redirect
    return Response(headers={"HX-Redirect": "/dashboard"})
# Return JSON for API clients
return ResumeResponse(id=resume.id, name=resume.name)
```

### Out-of-Band Swaps
Update multiple page sections in a single response:
```python
html_content = f"""<div id="resume-list" hx-swap-oob="true">{list_html}</div>
<div id="resume-detail">{detail_html}</div>"""
return HTMLResponse(content=html_content)
```

### Common HTMX Attributes
- `hx-get`, `hx-post`, `hx-put`, `hx-delete` - HTTP methods
- `hx-target` - Element to update
- `hx-swap` - How to swap (innerHTML, outerHTML, beforeend)
- `hx-swap-oob="true"` - Out-of-band swap for multiple elements
- `hx-confirm="Are you sure?"` - Confirmation dialogs
- `hx-indicator="#spinner"` - Loading state (use with `htmx-indicator` class)
- `hx-trigger="keyup changed delay:500ms"` - Auto-save pattern
- `hx-on::after-request="this.reset()"` - Form reset after submission

### Form Patterns
Form classes use `Form(...)` parameters:
```python
class UpdateResumeForm:
    def __init__(
        self,
        name: str = Form(...),
        content: str | None = Form(None),
    ):
        self.name = name
        self.content = content
```

### Template Organization
```
resume_editor/app/templates/
├── layouts/base.html      # Base layout with HTMX script
├── partials/              # HTMX partials (prefix with _)
│   ├── resume/
│   │   ├── _resume_list.html
│   │   ├── _resume_detail.html
│   │   └── _refine_result.html
│   └── admin/
├── pages/                 # Full page templates
├── dashboard.html
├── editor.html
└── refine.html
```

**Convention:** Use `_` prefix for partial templates meant for HTMX swapping.

### Resource Dependencies
Use custom dependencies to inject validated resources:
```python
async def get_resume_for_user(
    resume_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user_from_cookie)],
) -> DatabaseResume:
    """Get resume and validate it belongs to current user."""
    return get_resume_by_id_and_user(db, resume_id=resume_id, user_id=current_user.id)

# Usage in route
@router.put("/{resume_id}")
async def update_resume(
    resume: Annotated[DatabaseResume, Depends(get_resume_for_user)],
):
    # Resume is already validated and loaded
```

## SSE (Server-Sent Events) Patterns

### Helper Functions
Located in `route_logic/resume_ai_logic.py`:
- `create_sse_message(event, data)` - Format SSE message
- `create_sse_progress_message(message)` - Progress updates
- `create_sse_error_message(message)` - Error notifications
- `create_sse_done_message(html)` - Final result
- `create_sse_close_message()` - Stream completion

### SSE Endpoint Pattern
```python
@router.get("/{resume_id}/refine/stream")
async def refine_resume_stream(...) -> StreamingResponse:
    return StreamingResponse(
        _experience_refinement_stream(params),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

### SSE Template Pattern
HTMX POST returns loader fragment, GET initiates stream:
```html
<div id="refine-sse-loader"
     hx-ext="sse"
     sse-connect="/api/resumes/{{ resume_id }}/refine/stream?..."
     sse-swap="done,error"
     sse-close="close"
     hx-swap="outerHTML">
    <ul sse-swap="progress" hx-swap="beforeend"></ul>
</div>
```

## Common Tasks

### Adding a New Resume Section
1. Update the Markdown schema in `resume_writer` docs
2. Add form handlers in routes
3. Create HTMX templates for editing
4. Ensure validation aligns with `BasicBlockParse` patterns

### Adding AI Refinement Features
1. Create LLM prompt with `PydanticOutputParser`
2. Add SSE endpoint for progress updates
3. Implement per-item refinement (see Experience section pattern)
4. Reconstruct full resume before generating summaries

### Database Changes
1. Update SQLAlchemy models
2. Create Alembic migration: `uv run alembic revision --autogenerate -m "description"`
3. Apply: `uv run alembic upgrade head`
4. Update any affected Pydantic schemas

## Testing Patterns

- Tests in `./tests/` (never in `./resume_editor/tests/`)
- Use `pytest` with `uv run pytest tests`
- Mock FastAPI dependencies via `app.dependency_overrides`
- Set logging level to DEBUG for tests
- **Unique test filenames mandatory** - check `code_test_mappings.md`

### Test File Naming Exception
There are cases where test files cannot be named exactly like the source file. For example:
- `user.py` → `test_user_route.py` (not `test_user.py`)
- This prevents naming collisions during test collection
- **Always** update `code_test_mappings.md` when creating new mappings

### Mocking FastAPI Dependencies
```python
from resume_editor.app.api.routes.target_module import get_db

mock_db = Mock()
def get_mock_db():
    yield mock_db

app.dependency_overrides[get_db] = get_mock_db
# ... test ...
app.dependency_overrides.clear()
```

### Testing HTMX Routes
Set the `HX-Request` header to test HTMX-specific behavior:
```python
def test_update_resume_htmx(client, mock_db):
    response = client.put(
        "/api/resumes/1",
        data={"name": "Updated", "content": "# Resume"},
        headers={"HX-Request": "true"}
    )
    assert response.status_code == 200
    assert "hx-swap-oob" in response.text
```

## Code Conventions

See `CONVENTIONS.md` for exhaustive details. Key highlights:

- **Imports**: Always at top, never inline
- **Type hints**: Mandatory on all functions
- **Quotes**: Double quotes for strings
- **Logging**: Use `log.debug` at function start and before return, never f-strings
- **Functions**: Short, single-purpose, easily mockable
- **Paths**: Use `pathlib`, not `os.path`
- **Variables**: Remove unused variables
- **Templates**: HTML belongs in templates, not Python strings

## FastAPI Response Types

Due to some versioning conflicts, using `TemplateResponse` as a return type is currently broken.

Set `response_class=HTMLResponse` and `response_model=None` when returning templates:
```python
@router.get("/dashboard", response_class=HTMLResponse, response_model=None)
async def dashboard(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "dashboard.html", {})
```

## File Organization

```
resume_editor/
├── app/
│   ├── api/routes/      # FastAPI routes
│   ├── templates/       # HTML templates
│   ├── models.py        # SQLAlchemy models
│   └── schemas.py       # Pydantic schemas
└── ...
tests/                   # All tests (mirrors structure)
```

Keep files under 1000 lines. Split into modules as needed.

## Export Formats

- **Markdown**: Validated raw format
- **DOCX ATS_FRIENDLY**: Optimized for applicant tracking systems
- **DOCX PLAIN**: Simple formatted document

## Common Pitfalls

1. **Forgetting SSE for AI tasks**: Any LLM operation needs real-time progress feedback
2. **Inline HTML**: Keep markup in templates, not Python code
3. **Wrong test directory**: Tests go in `./tests/`, never nested in source
4. **Missing format_instructions**: Every LLM call needs explicit output formatting
5. **Not using Annotated**: FastAPI dependency injection must use `Annotated` pattern
6. **resume_writer availability**: Don't add checks for this module - it should always be there
