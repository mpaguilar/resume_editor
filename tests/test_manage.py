import logging
import runpy
import subprocess
from unittest.mock import patch

from click.testing import CliRunner

from manage import cli, main

log = logging.getLogger(__name__)


def test_generate_migration_success():
    """Test the generate-migration command successfully generates a migration."""
    runner = CliRunner()
    with patch("subprocess.run") as mock_run:
        result = runner.invoke(cli, ["generate-migration", "-m", "test migration"])
        assert result.exit_code == 0
        assert "Generating new migration..." in result.output
        assert "Successfully generated new migration: test migration" in result.output
        mock_run.assert_called_once_with(
            ["alembic", "revision", "--autogenerate", "-m", "test migration"], check=True
        )


def test_generate_migration_called_process_error():
    """Test the generate-migration command handles CalledProcessError."""
    runner = CliRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        result = runner.invoke(cli, ["generate-migration", "-m", "test migration"])
        assert result.exit_code == 0
        assert "An error occurred while generating migration:" in result.output


def test_generate_migration_file_not_found_error():
    """Test the generate-migration command handles FileNotFoundError."""
    runner = CliRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError
        result = runner.invoke(cli, ["generate-migration", "-m", "test migration"])
        assert result.exit_code == 0
        assert (
            "Error: 'alembic' command not found. Make sure Alembic is installed and in your PATH."
            in result.output
        )


def test_generate_migration_missing_message():
    """Test the generate-migration command fails if the message is missing."""
    runner = CliRunner()
    result = runner.invoke(cli, ["generate-migration"])
    assert result.exit_code != 0
    assert "Missing option" in result.output
    assert "--message" in result.output


def test_apply_migrations_success():
    """Test the apply-migrations command successfully applies migrations."""
    runner = CliRunner()
    with patch("subprocess.run") as mock_run:
        result = runner.invoke(cli, ["apply-migrations"])
        assert result.exit_code == 0
        assert "Applying database migrations..." in result.output
        assert "Successfully applied all migrations." in result.output
        mock_run.assert_called_once_with(["alembic", "upgrade", "head"], check=True)


def test_apply_migrations_called_process_error():
    """Test the apply-migrations command handles CalledProcessError."""
    runner = CliRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        result = runner.invoke(cli, ["apply-migrations"])
        assert result.exit_code == 0
        assert "An error occurred while applying migrations:" in result.output


def test_apply_migrations_file_not_found_error():
    """Test the apply-migrations command handles FileNotFoundError."""
    runner = CliRunner()
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError
        result = runner.invoke(cli, ["apply-migrations"])
        assert result.exit_code == 0
        assert (
            "Error: 'alembic' command not found. Make sure Alembic is installed and in your PATH."
            in result.output
        )


@patch("manage.cli")
def test_main(mock_cli):
    """Test that main calls cli."""
    main()
    mock_cli.assert_called_once_with()
