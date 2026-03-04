# Resume Editor

A web-based multi-user resume authoring, editing, and export application built with Python 3.12, FastAPI, and HTMX. Users can create resumes in Markdown format and leverage LLM assistance for refinement and export to DOCX.

## Features

- **User Management**: Secure user registration, login (username/password), logout, and role-based access control (`user`, `admin`). Includes encrypted storage for user settings and API keys. An initial setup wizard is enforced on first run to create the administrator account.

- **Admin Interface**: HTMX-powered web UI for administrators to manage users (create, list, edit, delete), assign roles, enforce password changes, and impersonate users for troubleshooting.

- **Resume Dashboard**: Weekly date-based pagination with text filtering. Manage base resumes (templates) and refined resumes (AI-enhanced for specific job applications). Sort by name, creation date, update date, or company.

- **Resume Editor**: Edit resume content in Markdown format with a dedicated text editor. Toggle inclusion of specific jobs/projects and filter work experience by date.

- **AI Refinement**: Refine experience sections against a job description with real-time progress updates via Server-Sent Events (SSE). Features include:
  - Per-role LLM refinement with automatic retry (3 attempts)
  - Running log/checkpoint system for failure recovery
  - AI-generated banner based on refined experience
  - Three post-refinement actions: Accept, Discard, or Save As New

- **Export Formats**: Download resumes in Markdown or DOCX formats:
  - `ATS_FRIENDLY`: Optimized for applicant tracking systems
  - `PLAIN`: Simple formatted document

## Documentation

- **[AGENTS.md](./AGENTS.md)** - Application overview, user flows, features, and high-level concepts
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Technical implementation details, HTMX/SSE patterns, testing patterns, module organization
- **[CONVENTIONS.md](./CONVENTIONS.md)** - Coding standards, style guide, ruff linting rules, and development practices

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy, Alembic
- **Frontend**: HTMX (server-side rendered), Tailwind CSS
- **Database**: PostgreSQL
- **AI/LLM**: LangChain with OpenAI-compatible endpoints
- **Export**: python-docx, resume-writer library
- **Testing**: pytest with async support
- **Package Management**: uv

## Prerequisites

- [Python 3.12](https://www.python.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [uv](https://github.com/astral-sh/uv) (for project and virtual environment management)
- [Docker](https://www.docker.com/) (optional, for containerized deployment)

## Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd resume-editor
   ```

2. **Create and activate a virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   uv sync
   ```

4. **Download Required NLTK Data:**
   ```bash
   uv run python -m nltk.downloader punkt
   ```

5. **Set up environment variables:**

   Create a `.env` file in the project root:

   ```dotenv
   # PostgreSQL connection details
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=resume_editor
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password

   # Security keys - CHANGE THESE IN PRODUCTION
   # Generate with: python -c 'import secrets; print(secrets.token_hex(32))'
   SECRET_KEY=a_very_secret_key_that_you_should_change

   # Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
   ENCRYPTION_KEY=AbCdEfGh-dnTvz6zpAFzf_mI98e5M_umgm17oY_1234=

   # (Optional) LLM configuration
   LLM_API_KEY=your_llm_api_key_here
   ```

## Database Management

This project uses Alembic for database schema migrations, managed through `manage.py`.

### Initial Setup

1. **Create the Database:**
   ```sql
   CREATE DATABASE resume_editor;
   ```

2. **Apply Migrations:**
   ```bash
   uv run python manage.py apply-migrations
   ```

3. **Create Initial Admin User:**
   
   Via web setup (recommended): Run the application and navigate to `/setup`
   
   Or via command line:
   ```bash
   uv run python manage.py create-admin --username admin
   ```

### Generating New Migrations

When you modify SQLAlchemy models:
```bash
uv run python manage.py generate-migration -m "Description of changes"
```

Always review the generated migration script in `alembic/versions/` before applying.

## Running the Application

### Development Server

```bash
uv run uvicorn resume_editor.app.main:app --reload
```

The application will be available at `http://localhost:8000`.

### Production with Gunicorn

```bash
uv run gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 "resume_editor.app.main:create_app()"
```

**Note:** In production, manage environment variables securely through your hosting provider.

### Running with Docker

1. **Build the Docker image:**
   ```bash
   docker build -t resume-editor . -f docker/Dockerfile
   ```

2. **Run the Docker container:**
   ```bash
   docker run -d --env-file .env -p 8000:8000 --name resume-editor-app resume-editor
   ```

Ensure the database is accessible from the container (set `DB_HOST` to `host.docker.internal` on Docker Desktop or use a containerized PostgreSQL).

## Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov

# Run specific test file
uv run pytest tests/app/api/routes/test_resume.py
```

## Code Quality

This project uses ruff for linting and formatting:

```bash
# Check all files
uv run ruff check

# Auto-fix issues
uv run ruff check --fix

# Check specific file
uv run ruff check resume_editor/app/models.py
```

See [CONVENTIONS.md](./CONVENTIONS.md) for detailed coding standards.

## Project Structure

```
resume_editor/
├── app/
│   ├── api/routes/          # FastAPI route handlers
│   ├── llm/                 # LLM orchestration modules
│   ├── templates/           # HTML templates (HTMX)
│   ├── models.py            # SQLAlchemy models
│   └── schemas.py           # Pydantic schemas
├── alembic/versions/        # Database migrations
└── ...

tests/                       # Test suite (mirrors app structure)
```

## Key Concepts

- **Base Resumes** (`is_base=true`): Starting templates for refinement. Never display a Company field.
- **Refined Resumes** (`is_base=false`): AI-enhanced versions targeting specific job applications. Include Company field and link to parent base resume.

See [AGENTS.md](./AGENTS.md) for detailed user flows and feature documentation.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License. See the LICENSE file for details.
