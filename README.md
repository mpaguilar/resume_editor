# Resume Editor

A web-based application for multi-user resume authoring, editing, and export, utilizing Markdown format and LLM assistance.

## Features

- **User Management**: Secure user registration, login, and settings management.
- **Resume Management**: Create, upload, edit, and save resumes in Markdown format.
- **Dynamic Editing**: HTMX-powered frontend for a seamless editing experience.
- **LLM Integration**: Refine resume content with AI assistance.
- **Multiple Export Formats**: Download resumes as validated Markdown or various DOCX formats.
- **Database Migrations**: Alembic-based schema management.

## Getting Started

Follow these instructions to set up the project for local development.

### Prerequisites

- [Python 3.12](https://www.python.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [uv](https://github.com/astral-sh/uv) (for project and virtual environment management)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd resume-editor
    ```

2.  **Create a virtual environment:**
    ```bash
    uv venv
    ```

3.  **Activate the virtual environment:**
    ```bash
    source .venv/bin/activate
    ```

4.  **Install dependencies:**
    ```bash
    uv sync
    ```

5.  **Set up environment variables:**

    Create a `.env` file in the project root by copying the example below. This file is used to configure the application.

    ```dotenv
    # .env
    DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/resume_editor
    SECRET_KEY=a_very_secret_key_that_you_should_change
    LLM_API_KEY=your_llm_api_key_here
    ```

    - **`DATABASE_URL`**: Your PostgreSQL connection string. Make sure the database `resume_editor` exists.
    - **`SECRET_KEY`**: A secret key for signing JWT tokens. You can generate a secure key with:
      ```bash
      python -c 'import secrets; print(secrets.token_hex(32))'
      ```
    - **`LLM_API_KEY`**: (Optional) Your API key for an OpenAI-compatible LLM service.

## Database Management

This project uses Alembic for database schema migrations, managed through `manage.py`.

### Initial Setup

Before running the application, you need to create the database in PostgreSQL. For example, using `psql`:
```sql
CREATE DATABASE resume_editor;
```

### Applying Migrations

To apply all pending migrations and bring the database schema up to date, run:
```bash
uv run python manage.py apply-migrations
```
This should be done after the initial setup and any time you pull new changes that include database migrations.

### Generating New Migrations

When you modify a SQLAlchemy model (e.g., in `resume_editor/app/models/`), you must generate a new migration script:
```bash
uv run python manage.py generate-migration -m "A short description of the change"
```
This will create a new migration file in `alembic/versions/`. Always review the generated script to ensure it's correct.

### Downgrading Migrations

To revert a migration, you can use `alembic` directly.

- **Revert the last migration:**
  ```bash
  uv run alembic downgrade -1
  ```

- **Revert all migrations:**
  ```bash
  uv run alembic downgrade base
  ```

## Running the Application

### Development Server

To run the application locally with auto-reloading, use `uvicorn`:
```bash
uv run uvicorn resume_editor.app.main:app --reload
```
The application will be available at `http://localhost:8000`.

### Production

For a production deployment, use a production-ready ASGI server like Gunicorn with Uvicorn workers.
```bash
uv run gunicorn -k uvicorn.workers.UvicornWorker resume_editor.app.main:app
```
**Note:** In a production environment, ensure you manage environment variables securely (e.g., through your hosting provider's configuration) and do not use a `.env` file. You will also need to configure the host, port, and number of workers according to your server's resources.

## Running Tests

To run the full test suite, use `pytest`:
```bash
uv run pytest tests/
```
