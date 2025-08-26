from unittest.mock import patch

from fastapi.testclient import TestClient

from resume_editor.app.main import create_app, main


def test_health_check():
    """Test that the health check endpoint returns 200 OK."""
    app = create_app()
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("resume_editor.app.main.create_app")
@patch("resume_editor.app.main.initialize_database")
def test_main(mock_initialize_database, mock_create_app):
    """Test that the main function calls create_app and initialize_database."""
    main()
    mock_create_app.assert_called_once()
    mock_initialize_database.assert_called_once()
