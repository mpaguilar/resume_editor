import logging
import subprocess

import click

from resume_editor.app.api.routes.route_logic.admin_crud import create_initial_admin
from resume_editor.app.database.database import get_session_local


log = logging.getLogger(__name__)


@click.group()
def cli():
    """Management script for the Resume Editor application."""
    pass


@cli.command("generate-migration")
@click.option(
    "-m",
    "--message",
    required=True,
    help="A short message describing the migration.",
)
def generate_migration(message: str):
    """
    Generate a new database migration script.

    This command wraps 'alembic revision --autogenerate'.

    Args:
        message (str): A short message describing the migration.

    Returns:
        None

    Notes:
        1. Executes the 'alembic revision --autogenerate' command as a subprocess.
        2. On success, prints a success message.
        3. On failure, catches exceptions and prints an error message.

    """
    _msg = "generate_migration starting"
    log.debug(_msg)
    click.echo("Generating new migration...")
    try:
        command = ["alembic", "revision", "--autogenerate", "-m", message]
        subprocess.run(command, check=True)
        _success_msg = f"Successfully generated new migration: {message}"
        click.echo(_success_msg)
        log.info(_success_msg)
    except subprocess.CalledProcessError as e:
        _error_msg = f"An error occurred while generating migration: {e}"
        click.echo(_error_msg, err=True)
        log.exception(_error_msg)
    except FileNotFoundError:
        _error_msg = "Error: 'alembic' command not found. Make sure Alembic is installed and in your PATH."
        click.echo(_error_msg, err=True)
        log.exception(_error_msg)
    _msg = "generate_migration returning"
    log.debug(_msg)


@cli.command("apply-migrations")
def apply_migrations():
    """
    Apply all pending migrations to the database.

    This command wraps 'alembic upgrade head'.

    Args:
        None

    Returns:
        None

    Notes:
        1. Executes the 'alembic upgrade head' command as a subprocess.
        2. On success, prints a success message.
        3. On failure, catches exceptions and prints an error message.

    """
    _msg = "apply_migrations starting"
    log.debug(_msg)
    click.echo("Applying database migrations...")
    try:
        command = ["alembic", "upgrade", "head"]
        subprocess.run(command, check=True)
        _success_msg = "Successfully applied all migrations."
        click.echo(_success_msg)
        log.info(_success_msg)
    except subprocess.CalledProcessError as e:
        _error_msg = f"An error occurred while applying migrations: {e}"
        click.echo(_error_msg, err=True)
        log.exception(_error_msg)
    except FileNotFoundError:
        _error_msg = "Error: 'alembic' command not found. Make sure Alembic is installed and in your PATH."
        click.echo(_error_msg, err=True)
        log.exception(_error_msg)
    _msg = "apply_migrations returning"
    log.debug(_msg)


@cli.command("create-admin")
@click.option("--username", required=True, help="Username for the admin user.")
@click.option(
    "--password",
    required=True,
    prompt=True,
    hide_input=True,
    confirmation_prompt=True,
    help="Password for the admin user.",
)
def create_admin(username: str, password: str):
    """
    Create an initial administrator account.

    Args:
        username (str): The username for the new admin user.
        password (str): The password for the new admin user.

    Returns:
        None

    Notes:
        1. Establishes a database connection.
        2. Calls the `create_initial_admin` function to create the user.
        3. Prints a success message or an error message.

    """
    _msg = "create_admin starting"
    log.debug(_msg)
    click.echo(f"Creating admin user '{username}'...")

    db_session_local = get_session_local()
    db = db_session_local()
    try:
        user = create_initial_admin(db=db, username=username, password=password)
        _success_msg = f"Admin user '{user.username}' created successfully."
        click.echo(_success_msg)
        log.info(_success_msg)
    except Exception as e:
        _error_msg = f"Error creating admin user: {e}"
        click.echo(_error_msg, err=True)
        log.exception(_error_msg)
    finally:
        db.close()

    _msg = "create_admin returning"
    log.debug(_msg)


def main():
    """Run the command line interface."""
    cli()


if __name__ == "__main__":
    main()
