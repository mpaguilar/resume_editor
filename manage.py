import logging
import subprocess

import click

log = logging.getLogger(__name__)


@click.group()
def cli():
    """Management script for the Resume Editor application."""
    pass


@cli.command("generate-migration")
@click.option("-m", "--message", required=True, help="A short message describing the migration.")
def generate_migration(message: str):
    """Generate a new database migration script.

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
    """Apply all pending migrations to the database.

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


def main():
    """Run the command line interface."""
    cli()


if __name__ == "__main__":
    main()
