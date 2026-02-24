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

## AI Refinement User Flow

Understanding the exact user experience is critical when working on AI refinement features.

### User Journey

```
Dashboard ──[Edit]──> Editor ──[Refine with AI]──> Refine Page ──[Start Refinement]──> SSE Progress Stream
```

### Step-by-Step Flow

**1. Dashboard Entry Point** (`/dashboard`)
- User sees list of their resumes
- Base resumes show **[Refine]** button (purple) before **[Edit]** button - goes directly to refine page
- Base resumes (is_base=true) are the starting point for refinement
- Refined resumes show **[View]** button instead (no Refine button)

**2. Editor Page** (`/resumes/{id}/edit`)
- Shows resume content in a text area for manual editing
- **"Refine with AI" button** is visible ONLY for base resumes (`{% if resume.is_base %}`)
- User can also Export (Markdown or DOCX) from here

**3. View Page** (`/resumes/{id}/view`)
- Displays a refined resume's content (read-only view)
- **"New refinement" button** appears next to "Export" for refined resumes (`{% if not resume.is_base %}`)
  - Enabled when `resume.parent_id` exists - links to `/resumes/{parent_id}/refine`
  - Disabled (gray) with tooltip when `resume.parent_id` is null - "No base resume available for this refined resume"
- Base resumes do NOT show this button (they use the dashboard "Refine" button instead)

**4. Refine Page** (`/resumes/{id}/refine`)
- Simple form with two inputs:
  - **Years Limit** (small text box, optional): Limits which experience roles are refined by date
  - **Job Description** (large textarea, required): The job posting text to align with
- **"Start Refinement"** button initiates the process
- **NO changes are made to the resume yet** - user is just configuring the refinement

**5. SSE Stream Processing**

When user clicks "Start Refinement", the form POSTs to `/api/resumes/{id}/refine/stream` which returns an SSE loader fragment. This establishes an SSE connection to `GET /api/resumes/{id}/refine/stream` with the job description and optional year limit as query parameters.

The user sees real-time progress messages:

| Order | Progress Message | What's Happening |
|-------|-----------------|------------------|
| 1 | "Parsing resume..." | Extracting experience roles from Markdown |
| 2 | "Analyzing job description..." | LLM call to analyze job requirements |
| 3 | "Job analysis complete" | Job analysis finished |
| 4 | "Refining role 'Title @ Company'..." | **Per-role LLM refinement** (one per role) |
| 5 | "Generating AI introduction..." | Creating banner based on refined content |
| 6 | Final result display | Shows refined resume with Accept/Discard/Save As New |

### Critical User Experience Point

**The user waits passively during refinement.** They do not:
- Edit the job description mid-process
- Cancel individual roles
- Interact with the page until completion or error

**When errors occur:** The SSE stream shows retry attempts. If all retries fail, it terminates with an error message. The user sees retry progress and/or the error message in the progress list. If they click "Start Refinement" again, the process **resumes from checkpoint** and skips already-refined roles.

### Failure Modes

There are two observed failure patterns during refinement:

**Failure Mode A: LLM Response Error (With Automatic Retry)**
- **Symptom:** SSE stream shows retry messages like "[Attempt 1 failed: Empty response. Retrying in 3s...]" followed by eventual error or success
- **Behavior:** System automatically retries up to 3 times (1 initial + 2 retries) with 3-second delays between attempts
- **Recovery:** If all retries fail, stream terminates with error. User clicks "Start Refinement" to resume from checkpoint (skips already-refined roles)
- **Cause:** LLM returns empty or non-JSON response, causing `JSONDecodeError` in `refine_role()`. Retry mechanism handles transient failures.

**Failure Mode B: Stream Loop/Repetition**
- **Symptom:** Progress messages start repeating - user sees "Parsing resume..." again after already seeing role refinement progress
- **Behavior:** SSE stream continues but restarts the entire refinement sequence from step 1
- **Recovery:** User can click "Cancel" button to stop the stream, then click "Start Refinement" again
- **Cause:** Unknown - intermittent, not captured in logs yet

**Important UX Notes:**
- Browser refresh during refinement = intentional feature to start over
- Automatic retry mechanism - up to 3 attempts with 3-second delays for transient LLM failures
- Resume cannot be edited during refinement (no UI for it), so resume state is stable
- User cannot change job description mid-refinement - they must cancel and start new refinement

### Running Log / Checkpoint System

To enable recovery from failures and enhanced banner generation, the system maintains a **running log** of refined roles:

**Purpose:**
1. **Failure Recovery:** If refinement fails partway through, already-refined roles are preserved and skipped on retry
2. **Banner Enhancement:** Accumulated role data (skills, companies) is used to generate more accurate, context-rich banners

**Terminology:**
- **Job Description**: Text the user enters in the "Job Description" textarea (the target job posting)
- **Role**: An experience entry from the resume (company, title, dates, description, skills)

**Lifecycle:**
- **Created:** Empty list when user clicks "Start Refinement"
- **Populated:** As each role is successfully refined (appended to list in real-time)
- **Persisted:** Server-side only, survives retry attempts (browser refresh clears it)
- **Cleared:** When refinement completes successfully AND new resume is generated, or if job description changes

**Data Captured Per Role:**
- Original index (position in resume)
- Company name
- Job title
- Refined description (summary, responsibilities)
- Relevant skills (extracted during refinement)
- Start/end dates
- Timestamp of refinement

**Recovery Behavior:**
- When user clicks "Start Refinement" again after a failure (new HTTP request), check for existing running log from previous request
- If log exists, skip already-refined roles
- Job analysis is cached and reused (no duplicate LLM call)
- Concurrent refinement continues with only unrefined roles
- Stream shows "Resuming from previous attempt..." then continues with "Refining role 'Title @ Company'..."
- If no log exists (first attempt), start fresh with empty list and new job analysis

**Button State Management:**
- "Start Refinement" button is **disabled** while refinement is in progress
- Button is **re-enabled** when refinement completes (success or failure)
- User can click again after an error to resume from where it failed
- User can click again after success to start a completely new refinement

**Log Lifecycle:**
- Created empty when "Start Refinement" is clicked
- Populated as each role is successfully refined
- Used to resume if refinement fails (error occurs)
- Discarded when:
  - Refinement completes successfully (refined resume returned)
  - User navigates away or refreshes the page
  - User explicitly cancels and restarts

### Retry Mechanism

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
- Located in `refine_role()` in `resume_editor/app/llm/orchestration.py`
- Helper functions: `_is_retryable_error()`, `_handle_retry_delay()`, `_log_failed_attempt()`
- Progress callbacks via `progress_callback` parameter for SSE updates

### Refinement Scope

**What gets refined:**
- ✓ Introduction/Banner (regenerated based on refined experience)
- ✓ Experience roles (each role's summary, responsibilities, skills)

**What does NOT get refined:**
- ✗ Personal information (name, contact, etc.)
- ✗ Education section
- ✗ Certifications
- ✗ Projects (preserved but not refined)

### Banner Generation Output Format

The AI-generated banner uses a **role-centric evidence extraction** approach that leverages data from the `RunningLog`:

**Format:**
- **Bold prefix format:** Each bullet starts with `**Category:** Description`
- **Maximum 5 brief bullets** (usually 3-5)
- **Semantic grouping:** Related skills are grouped under coherent themes

**Data Sources:**
1. **Experience Section (from RunningLog):**
   - Uses `RefinedRoleRecord` data for each refined role
   - Company, title, relevant skills, and refined description
   - Skills already filtered for job relevance during refinement

2. **Cross-Section Evidence (from raw resume):**
   - **Education:** Conditionally included only if directly relevant to job
   - **Certifications:** Integrated where they strengthen skill categories
   - **Projects:** Mentioned if they demonstrate job-relevant skills not in work experience

**Example Output:**
```markdown
- **Enterprise Architecture:** Designed cloud-native solutions using AWS and Azure (*Company A*, *Company B*)
- **Technical Leadership:** Led teams of 5-10 engineers across multiple projects (*Company C*, *Company D*)
- **Certifications:** AWS Solutions Architect, Azure Administrator
- **Education:** BS Computer Science, MS Data Science (only if relevant)
```

**Key Principles:**
- 100% factual accuracy - no invented skills or experiences
- Company associations shown in parenthetical format with **italicized** company names: "Skill (*Company A*, *Company B*)"
- Job-relevant skills prioritized and appear first
- No mixing of unrelated technologies in the same bullet
- Honest representation with qualifying language when appropriate

### User Actions After Refinement

After successful refinement, the user sees the refined resume and has three options:

1. **Accept** - Updates the current base resume with refined content
2. **Discard** - Redirects back to editor, no changes saved
3. **Save As New** - Creates a new refined resume (child of base), keeps base unchanged

### Key Files for AI Refinement

```
resume_editor/app/api/routes/resume_ai.py              # SSE endpoints
resume_editor/app/api/routes/route_logic/resume_ai_logic.py  # Core refinement logic
resume_editor/app/llm/orchestration.py                 # LLM calls and concurrency
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
7. **Required form fields for settings updates**: Settings forms with masked fields (like API keys) must use optional form parameters (`str | None = None`) to allow partial updates without re-entering sensitive data. See `update_settings` in `resume_editor/app/web/pages.py` for the correct pattern.
