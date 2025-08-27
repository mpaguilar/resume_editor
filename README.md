# Resume Editor

A web-based application for multi-user resume authoring, editing, and export, utilizing Markdown format and LLM assistance.

## Database Migrations

This project uses Alembic to manage database migrations.

### Creating a New Migration

When you change a SQLAlchemy model (e.g., in `resume_editor/app/models/`), you need to create a new migration script. Run the following command:

```bash
uv run alembic revision --autogenerate -m "A short description of the change"
```

This will generate a new file in `alembic/versions/`. Review this file to ensure it's correct.

### Applying Migrations

To apply migrations to your database, run:

```bash
uv run alembic upgrade head
```

This should be done when setting up the application for the first time and after pulling new changes that include database migrations.
