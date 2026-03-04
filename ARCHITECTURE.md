# Architecture Guide: Resume Editor

> **Application Overview**: For understanding what this application does, user flows, and high-level features, see [AGENTS.md](./AGENTS.md).

## Project Structure

### Directory Layout

- **Main application code**: `./resume_editor/` subdirectory
- **Root folder**: Project configuration files only (pyproject.toml, etc.)
- **Templates**: `resume_editor/app/templates/`
- **Tests**: `./tests/` (never create `./resume_editor/tests/`)

### Dependency Management

This project uses `uv` for dependency management:
- Python commands: `uv run pytest tests`, `uv run ruff check`
- Add dependencies: `uv add <package>`

### Key Dependencies

- **FastAPI**: Web framework
- **HTMX**: Frontend interactions (server-side rendered)
- **LangChain**: LLM processing and orchestration
- **PostgreSQL**: Database with Alembic migrations
- **resume_writer**: External library for resume parsing/export

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
    ├── resume_ai_logic.py               # Main exports for AI logic
    ├── resume_ai_logic_params.py        # Parameter dataclasses
    ├── resume_ai_logic_sse.py           # SSE message helpers
    ├── resume_ai_logic_helpers.py       # HTML generation helpers
    ├── resume_ai_logic_extraction.py    # Section extraction
    ├── resume_ai_logic_reconstruction.py  # Resume reconstruction
    ├── resume_ai_logic_streaming.py     # Stream event handlers
    ├── resume_serialization.py
    ├── resume_serialization_helpers.py
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

**Configuration:**
- API key from `LLM_API_KEY` environment variable
- Support custom OpenAI-compatible endpoints

**Required Patterns:**
- All LLM calls **must** use `PydanticOutputParser`
- All messages formatted for the LLM **must** include `format_instructions` parameter
- All responses **must** be parsed with `langchain_core.utils.json.parse_json_markdown`

**Libraries:**
- `langchain` and related libraries for LLM processing
- `langchain_community.retrievers.WikipediaRetriever` for Wikipedia searches

### Authentication & Security

- Role-based: `user` and `admin`
- Encrypted storage for API keys and sensitive settings
- Middleware enforces initial setup if no users exist
- Password change workflow can be mandatory
- User impersonation available for admins
- **Session Timeout Configuration**:
  - Global default: 600 minutes (10 hours) via `ACCESS_TOKEN_EXPIRE_MINUTES` env var in `config.py`
  - Per-user override: Stored in `user_settings.access_token_expire_minutes` (Integer, nullable)
  - Valid range: 15-1440 minutes (enforced in `settings_crud.py`)
  - Session refresh: Middleware extends session on each request via `refresh_session_middleware`

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

### HTMX Pagination Pattern

**Critical:** When using `hx-swap="outerHTML"` on a target element, the response MUST include the target element wrapper, or subsequent requests will fail.

**The Problem:**
Dashboard pagination uses `<div id="resume-list">` as the swap target. When `outerHTML` is used, the entire div is replaced. If the response doesn't include the wrapper div, subsequent pagination clicks fail because `#resume-list` no longer exists in the DOM.

**The Solution:**
The `_generate_resume_list_html()` function has a `wrap_in_div` parameter that controls whether the response includes the `<div id="resume-list">` wrapper:

```python
# For HTMX list requests (pagination) - MUST include wrapper
html_content = _generate_resume_list_html(
    base_resumes=base_resumes,
    refined_resumes=refined_resumes,
    # ... other params
    wrap_in_div=True,  # Critical for pagination to work
)

# For update responses (OOB swap) - no wrapper needed
html_content = _generate_resume_list_html(
    base_resumes=base_resumes,
    refined_resumes=refined_resumes,
    # ... other params
    wrap_in_div=False,  # OOB swap doesn't need wrapper
)
```

**Usage Guidelines:**
- Use `wrap_in_div=True` for HTMX requests that swap on `#resume-list` directly
- Use `wrap_in_div=False` for OOB (out-of-band) swaps where the list is updated as a side effect
- The wrapper div is required for pagination to work across multiple clicks

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

Located in `route_logic/resume_ai_logic_sse.py`:
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

## Retry Mechanism

The refinement process includes an **automatic retry mechanism** for transient LLM failures:

**Retry Configuration:**
- **Max attempts:** 3 total (1 initial + 2 retries)
- **Delay:** Fixed 3-second delay between retry attempts
- **Semaphore behavior:** Released during delay to allow other roles to proceed

**Retryable Errors:**
- `JSONDecodeError` - Empty or malformed JSON response from LLM
- `TimeoutError` - LLM call timeout
- `ConnectionError` - Network connectivity issues
- Rate limiting (HTTP 429)

**Non-Retryable Errors (fail immediately):**
- `AuthenticationError` - Invalid API key
- `ValidationError` - Pydantic schema validation failure
- `InvalidToken` - Encryption/decryption failure

**User Experience:**
- Progress messages show retry attempts: "[Attempt 1 failed: Empty response. Retrying in 3s...]"
- Final error message includes role context: "Unable to refine 'Title @ Company' after 3 attempts"
- Debug logging captures truncated LLM responses (first 500 chars) for troubleshooting

**Implementation:**
- Located in `refine_role()` in `resume_editor/app/llm/orchestration_refinement.py`
- Helper functions: `_is_retryable_error()`, `_handle_retry_delay()`, `_log_failed_attempt()`
- Progress callbacks via `progress_callback` parameter for SSE updates

### Button State Management

- "Start Refinement" button is **disabled** while refinement is in progress
- Button is **re-enabled** when refinement completes (success or failure)
- User can click again after an error to resume from where it failed
- User can click again after success to start a completely new refinement

## LLM Orchestration Module Structure

The LLM orchestration layer has been modularized into focused modules:

```
resume_editor/app/llm/
├── orchestration.py              # Main exports and coordination
├── orchestration_client.py       # LLM client initialization
├── orchestration_models.py       # Shared dataclasses (RefinementState, GeneratedBanner)
├── orchestration_analysis.py     # Job description analysis
├── orchestration_refinement.py   # Role refinement with retry logic
└── orchestration_banner.py       # Banner generation with cross-section evidence
```

### Key Files for AI Refinement

```
resume_editor/app/api/routes/resume_ai.py              # SSE endpoints
resume_editor/app/api/routes/route_logic/resume_ai_logic.py  # Main exports for AI logic
resume_editor/app/api/routes/route_logic/resume_ai_logic_streaming.py  # SSE streaming
resume_editor/app/llm/orchestration.py                 # Main exports for orchestration
resume_editor/app/llm/orchestration_client.py          # LLM client initialization
resume_editor/app/llm/orchestration_analysis.py        # Job analysis
resume_editor/app/llm/orchestration_refinement.py      # Role refinement with retry logic
resume_editor/app/llm/orchestration_banner.py          # Banner generation
resume_editor/app/templates/refine.html               # Refine page UI
resume_editor/app/templates/partials/resume/_refine_sse_loader.html  # SSE progress UI
resume_editor/app/templates/partials/resume/_refine_result.html      # Final result UI
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

**Mappings File:**
- Known mappings are tracked in `code_test_mappings.md`
- **Always** update `code_test_mappings.md` when creating new mappings

### Mocking FastAPI Dependencies

```python
from resume_editor.app.api.routes.target_module import get_db

@patch("resume_editor.app.api.routes.target_module.get_current_user")
@patch("resume_editor.app.api.routes.target_module.get_db")
def test_something():
    app = create_app()
    client = TestClient(app)

    mock_db = Mock()

    # mock the return value
    mock_db.query.return_value.filter.return_value.first.return_value = mock_result

    # These next lines are **very** important
    def get_mock_db():
        yield mock_db

    # note that we are overriding `get_db` here
    app.dependency_overrides[get_db] = get_mock_db

    # perform tests and assertions

    # clear the overrides
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

See [CONVENTIONS.md](./CONVENTIONS.md) for all coding standards, including:
- Import conventions and formatting
- Type hints and docstring requirements
- Logging patterns
- FastAPI dependency injection patterns
- Ruff linting rules

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

## Company and Notes Fields Implementation

For field behavior and validation rules, see [AGENTS.md](./AGENTS.md).

### Dashboard Integration

**Refined Resume Display Format:**
```
Resume Name — Company: Acme Corp
ID: 385 - Parent: 2
via gmail (User Name)
Created: 2026-02-24 • Updated: 2026-02-24
```

**Search/Filter:**
- Searches name, notes, AND company fields
- Case-insensitive partial matching
- Only applies to refined resumes (base resumes always shown)

**Sorting:**
- Can sort by company (ascending/descending)
- Base resumes maintain separate ordering

### Key Files

```
resume_editor/app/api/routes/resume_ai.py              # Refine page form handling
resume_editor/app/api/routes/route_logic/resume_validation.py  # Company/notes validation
resume_editor/app/web/pages.py                         # View page form handling
resume_editor/app/api/routes/html_fragments.py         # Dashboard list generation
```

### API Notes

When calling refinement endpoints, company and notes are:
1. Validated on the POST refine/stream endpoint
2. Passed through to the SSE stream
3. Saved to the refined resume upon completion
4. Editable on the result page before Accept/Save As New

## Related Documentation

- **Application Overview**: [AGENTS.md](./AGENTS.md) - User flows, features, high-level concepts
- **Code Conventions**: [CONVENTIONS.md](./CONVENTIONS.md) - Detailed coding standards and ruff rules
