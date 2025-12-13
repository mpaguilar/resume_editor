# Resume Editor

A web-based application for multi-user resume authoring, editing, and export, utilizing Markdown format and LLM assistance.

## Features

-   **User Management**: Secure user registration, login (username/password), logout, and role-based access control (`user`, `admin`). Includes a secure password change workflow and encrypted storage for user settings and API keys. An initial setup page is enforced on first run to create the administrator account.
-   **Admin Interface**: A dedicated, HTMX-powered web UI for administrators to manage users (create, list, edit, delete), assign roles, enforce password changes, and impersonate users for troubleshooting.
-   **Web Dashboard**: An HTMX-powered dashboard for users to manage their resumes. It provides a list of all resumes, a form to create new ones, and a dedicated settings page for managing LLM configurations and changing passwords.
-   **Dedicated Resume Editor**: A dedicated page for viewing and editing a single resume's Markdown content, with forms for editing structured data (personal info, education, experience, etc.).
-   **Resume Management**: Create, update, delete, and download resumes. Save LLM-refined content by overwriting an existing resume or creating a new one.
-   **Editing & Export**: Edit a resume's name and raw content, toggle the inclusion of specific jobs/projects, and filter work experience by date for export. Download resumes in Markdown or DOCX (`ATS_FRIENDLY`, `PLAIN`) formats.
-   **LLM Integration**: Refine the "Experience" section against a job description, with real-time progress updates via Server-Sent Events (SSE). Supports custom OpenAI-compatible API endpoints and models.

## Getting Started

Follow these instructions to set up the project for local development or run it with Docker.

### Prerequisites

-   [Python 3.12](https://www.python.org/)
-   [PostgreSQL](https://www.postgresql.org/)
-   [uv](https://github.com/astral-sh/uv) (for project and virtual environment management)
-   [Docker](https://www.docker.com/) (for containerized deployment)

### Local Development Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd resume-editor
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    uv sync
    ```

4.  **Download Required NLTK Data:**
    The application uses the NLTK library for text processing. Download the required data:
    ```bash
    uv run python -m nltk.downloader punkt
    ```

5.  **Set up environment variables:**

    Create a `.env` file in the project root by copying the example below. This file is used to configure the application.

    ```dotenv
    # .env - PostgreSQL connection details
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

    -   **`DB_*`**: Your PostgreSQL connection details.
    -   **`SECRET_KEY`**: A secret key for signing JWT tokens.
    -   **`ENCRYPTION_KEY`**: A secret key for encrypting sensitive data like user API keys.
    -   **`LLM_API_KEY`**: (Optional) Your API key for an OpenAI-compatible LLM service.

## Database Management

This project uses Alembic for database schema migrations, managed through `manage.py`.

### Initial Setup

1.  **Create the Database**: Before running the application, you need to create the database in PostgreSQL. For example, using `psql`:
    ```sql
    CREATE DATABASE resume_editor;
    ```

2.  **Apply Migrations**: To apply all pending migrations and bring the database schema up to date, run:
    ```bash
    uv run python manage.py apply-migrations
    ```

3.  **Create Initial Admin User**: The application is designed for a web-based first-time setup. Once you run the application for the first time (see below), you will be automatically redirected to a `/setup` page to create the first administrator account.

    Alternatively, you can create the admin user via the command line:
    ```bash
    uv run python manage.py create-admin --username admin
    ```

### Generating New Migrations

When you modify a SQLAlchemy model (e.g., in `resume_editor/app/models/`), you must generate a new migration script:
```bash
uv run python manage.py generate-migration -m "A short description of the change"
```
This will create a new migration file in `alembic/versions/`. Always review the generated script to ensure it's correct.

## Running the Application

### Development Server

To run the application locally with auto-reloading, use `uvicorn`:
```bash
uv run uvicorn resume_editor.app.main:app --reload
```
The application will be available at `http://localhost:8000`. Navigate to this URL to complete the initial admin user setup.

### Production with Gunicorn

For a production deployment, use a production-ready ASGI server like Gunicorn with Uvicorn workers.
```bash
uv run gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 "resume_editor.app.main:create_app()"
```
**Note:** In a production environment, ensure you manage environment variables securely (e.g., through your hosting provider's configuration) and do not use a `.env` file. You will also need to configure the host, port, and number of workers according to your server's resources.

### Running with Docker

You can also run the application using Docker, which simplifies deployment by packaging the application and its dependencies.

1.  **Build the Docker image:**
    ```bash
    docker build -t resume-editor . -f docker/Dockerfile
    ```

2.  **Run the Docker container:**

    Make sure your `.env` file is present in the project root, as the command below mounts it into the container.
    ```bash
    docker run -d --env-file .env -p 8000:8000 --name resume-editor-app resume-editor
    ```
    -   `-d` runs the container in detached mode.
    -   `--env-file .env` loads your environment variables from the `.env` file.
    -   `-p 8000:8000` maps port 8000 on your host to port 8000 in the container.

The application will be accessible at `http://localhost:8000`. You will still need to ensure the database is running and accessible from the Docker container (e.g., by setting `DB_HOST` to `host.docker.internal` on Docker Desktop or by running PostgreSQL in another container on the same network).

## Running Tests

To run the full test suite, use `pytest`:
```bash
uv run pytest tests/
```
