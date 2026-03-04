# Agent Guide: Resume Editor

> **Technical Implementation Details**: For architecture patterns, HTMX/SSE implementation specifics, and testing patterns, see [ARCHITECTURE.md](./ARCHITECTURE.md). For coding conventions and standards, see [CONVENTIONS.md](./CONVENTIONS.md).

## Project Overview

A web-based multi-user resume authoring, editing, and export application built with Python 3.12, FastAPI, and HTMX. Users can create resumes in Markdown format and leverage LLM assistance for refinement and export to DOCX.

## Key Dependencies

- **FastAPI**: Web framework with API routes
- **HTMX**: Dynamic frontend interactions (server-side rendered, no React/Vue)
- **Tailwind CSS**: Styling
- **PostgreSQL**: Data storage with Alembic migrations
- **resume_writer**: External library for parsing and exporting resumes

## Core Concepts

### Resume Types

**Base Resumes** (`is_base=true`)
- The starting point/template for refinement
- Created via manual editing or import
- Can be refined multiple times
- Never display a Company field (they're templates)

**Refined Resumes** (`is_base=false`)
- AI-enhanced versions of base resumes
- Created by running the AI refinement process
- Linked to a parent base resume via `parent_id`
- Include a Company field (target company for job application)

### Resume Data Flow

1. User creates/edits via HTMX forms
2. Stored as Markdown in PostgreSQL
3. Parsed using `resume_writer` for validation
4. LLM refinement happens on structured sections
5. Export to Markdown or DOCX (ATS_FRIENDLY, PLAIN formats)

## User Flows

### Dashboard Entry Point

**URL**: `/dashboard`

- User sees list of their resumes
- Base resumes show **[Refine]** button (purple) before **[Edit]** button - goes directly to refine page
- Refined resumes show **[View]** button instead (no Refine button)

### Editor Page

**URL**: `/resumes/{id}/edit`

- Shows resume content in a text area for manual editing
- **"Refine with AI" button** is visible ONLY for base resumes
- User can also Export (Markdown or DOCX) from here

### View Page

**URL**: `/resumes/{id}/view`

- Displays a refined resume's content (read-only view)
- **"New refinement" button** appears next to "Export" for refined resumes
  - Enabled when `resume.parent_id` exists - links to `/resumes/{parent_id}/refine`
  - Disabled (gray) with tooltip when `resume.parent_id` is null
- Base resumes do NOT show this button

### AI Refinement Flow

**URL**: `/resumes/{id}/refine`

**Step 1: Configuration**
Simple form with two inputs:
- **Years Limit** (optional): Limits which experience roles are refined by date
- **Job Description** (required): The job posting text to align with

**Step 2: Processing**
Clicking "Start Refinement" initiates an SSE stream with real-time progress:

| Order | Progress Message | What's Happening |
|-------|-----------------|------------------|
| 1 | "Parsing resume..." | Extracting experience roles from Markdown |
| 2 | "Analyzing job description..." | LLM call to analyze job requirements |
| 3 | "Job analysis complete" | Job analysis finished |
| 4 | "Refining role 'Title @ Company'..." | Per-role LLM refinement (one per role) |
| 5 | "Generating AI introduction..." | Creating banner based on refined content |
| 6 | Final result display | Shows refined resume with Accept/Discard/Save As New |

**Step 3: Post-Refinement Actions**

After successful refinement, the user sees the refined resume and has three options:

1. **Accept** - Updates the current base resume with refined content
2. **Discard** - Redirects back to editor, no changes saved
3. **Save As New** - Creates a new refined resume (child of base), keeps base unchanged

### Failure Recovery

The refinement process includes automatic retry for transient LLM failures:
- Up to 3 attempts with 3-second delays
- Progress messages show retry attempts
- If all retries fail, user can click "Start Refinement" again to resume from checkpoint
- Already-refined roles are skipped on retry

**User cannot:**
- Edit the job description mid-process
- Cancel individual roles
- Interact with the page until completion or error

### Running Log / Checkpoint System

To enable recovery from failures and enhanced banner generation, the system maintains a running log of refined roles:

- **Created:** Empty list when user clicks "Start Refinement"
- **Populated:** As each role is successfully refined
- **Persisted:** Server-side only, survives retry attempts
- **Cleared:** When refinement completes successfully, user navigates away, or job description changes

**Data Captured Per Role:**
- Original index (position in resume)
- Company name, job title
- Refined description (summary, responsibilities)
- Relevant skills (extracted during refinement)
- Start/end dates
- Timestamp of refinement

## Dashboard Features

### Pagination and Filtering

**Pagination:**
- Default view shows last 7 days (`week_offset=0`)
- Navigation: "Previous Week" / "Next Week" buttons
- Base resumes always shown regardless of date range

**Filtering:**
- Searches `name`, `notes`, and `company` fields
- Case-insensitive partial matching
- AND logic for multiple terms (all terms must match)
- Max 100 characters
- Applied only to refined resumes

**URL Parameters:**
- `week_offset` (int): Week offset from current
- `filter` (str): Search query string
- `sort_by` (enum): Sorting criterion

### Sorting Options

- name_asc / name_desc
- created_at_asc / created_at_desc
- updated_at_asc / updated_at_desc
- company_asc / company_desc (refined resumes only)

## Company and Notes Fields

### Overview

The resume editing workflow includes **Company** and **Notes** fields:

- **Company**: Target company for the job application (refined resumes only)
- **Notes**: User notes about the resume/refinement (editable on both base and refined)

### Field Behavior

**Base Resumes:**
- Never display company field
- Notes are editable but less commonly used

**Refined Resumes:**
- Company is set during refinement on the refine page
- Company and notes are editable on the view page
- Company always displays in dashboard (shows "N/A" if blank)

### Validation

- **Company**: Max 255 characters
- **Notes**: Max 5000 characters
- Validation occurs server-side on form submission

## Refinement Scope

**What gets refined:**
- ✓ Introduction/Banner (regenerated based on refined experience)
- ✓ Experience roles (each role's summary, responsibilities, skills)

**What does NOT get refined:**
- ✗ Personal information (name, contact, etc.)
- ✗ Education section
- ✗ Certifications
- ✗ Projects (preserved but not refined)

### Banner Generation

The AI-generated banner uses a **role-centric evidence extraction** approach:

**Format:**
- **Bold prefix format:** Each bullet starts with `**Category:** Description`
- **Maximum 5 brief bullets** (usually 3-5)
- **Semantic grouping:** Related skills are grouped under coherent themes

**Example Output:**
```markdown
- **Enterprise Architecture:** Designed cloud-native solutions using AWS and Azure (*Company A*, *Company B*)
- **Technical Leadership:** Led teams of 5-10 engineers across multiple projects (*Company C*, *Company D*)
- **Certifications:** AWS Solutions Architect, Azure Administrator
```

**Key Principles:**
- 100% factual accuracy - no invented skills or experiences
- Company associations shown in parenthetical format with **italicized** company names
- Job-relevant skills prioritized and appear first

## Job Analysis Extraction

During the refinement process, the LLM automatically extracts structured job details from the job description:

**Extracted Fields:**
- **company_name**: The hiring company (e.g., "Acme Corporation")
- **job_title**: The position title (e.g., "Senior Software Engineer")
- **pay_rate**: Salary or compensation information (e.g., "$150k-$200k")
- **contact_info**: Application contact details (e.g., "careers@company.com")
- **work_arrangement**: Remote/hybrid/onsite status (e.g., "Remote friendly")
- **location**: Job location (e.g., "Austin, TX")
- **special_instructions**: Unique application requirements (e.g., "Include portfolio link")

**Field Usage:**
- All fields are extracted automatically during job analysis (first step of refinement)
- Extracted values appear as editable textboxes on the refine result page
- **Company field** is pre-populated with `extracted_company_name` if available
- **Notes field** has `special_instructions` appended to it
- All extracted fields are persisted when saving the refined resume

**Edge Cases:**
- Fields that cannot be extracted appear as empty/null (not errors)
- User can edit all extracted values before saving
- Maximum lengths enforced: company_name (255), job_title (255), pay_rate (100), contact_info (500), work_arrangement (50), location (255), special_instructions (5000)

## Export Formats

- **Markdown**: Validated raw format
- **DOCX ATS_FRIENDLY**: Optimized for applicant tracking systems
- **DOCX PLAIN**: Simple formatted document

## Common Pitfalls

1. **Forgetting SSE for AI tasks**: Any LLM operation needs real-time progress feedback
2. **Inline HTML**: Keep markup in templates, not Python code
3. **Missing format_instructions**: Every LLM call needs explicit output formatting
4. **Not using Annotated**: FastAPI dependency injection must use `Annotated` pattern
5. **Required form fields for settings updates**: Settings forms with masked fields must use optional form parameters to allow partial updates

## Authentication & Security

- Role-based access: `user` and `admin`
- Encrypted storage for API keys and sensitive settings
- Middleware enforces initial setup if no users exist
- User impersonation available for admins
- **Session Timeout**: Configurable per-user (15-1440 minutes, default 600 minutes / 10 hours)
  - Global default: 600 minutes (10 hours) via `ACCESS_TOKEN_EXPIRE_MINUTES` env var
  - Per-user setting stored in `user_settings.access_token_expire_minutes`
  - Users can configure their timeout in Settings page
  - Automatic token refresh on each request (session extension)

## Further Reading

- **Technical Implementation**: [ARCHITECTURE.md](./ARCHITECTURE.md) - Architecture patterns, HTMX/SSE patterns, testing patterns, module organization
- **Coding Standards**: [CONVENTIONS.md](./CONVENTIONS.md) - Code conventions, style guide, ruff linting rules, and development practices
- **LLM Orchestration**: See `resume_editor/app/llm/orchestration*.py` modules for AI refinement implementation
