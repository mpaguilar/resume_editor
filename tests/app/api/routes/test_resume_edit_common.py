import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from resume_editor.app.api.dependencies import get_resume_for_user
from resume_editor.app.main import create_app


@pytest.fixture
def app():
    """A FastAPI app instance."""
    app = create_app()
    yield app
    app.dependency_overrides.clear()


@pytest.fixture
def client_with_auth_no_resume(app):
    def get_resume_for_user_not_found():
        raise HTTPException(status_code=404, detail="Resume not found")

    app.dependency_overrides[get_resume_for_user] = get_resume_for_user_not_found
    return TestClient(app)


@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/resumes/999/personal",
        "/api/resumes/999/education",
        "/api/resumes/999/experience",
        "/api/resumes/999/projects",
        "/api/resumes/999/certifications",
    ],
)
def test_get_info_not_found(client_with_auth_no_resume: TestClient, endpoint: str):
    """Test GET endpoints return 404 for a non-existent resume."""
    response = client_with_auth_no_resume.get(endpoint)
    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found"}


@pytest.mark.parametrize(
    "endpoint, payload",
    [
        ("/api/resumes/999/personal", {"name": "test"}),
        (
            "/api/resumes/999/education",
            {"degrees": [{"school": "test", "degree": "BSc"}]},
        ),
        (
            "/api/resumes/999/experience",
            {
                "roles": [
                    {
                        "basics": {
                            "company": "test",
                            "title": "t",
                            "start_date": "2023-01-01T00:00:00",
                        },
                    },
                ],
            },
        ),
        (
            "/api/resumes/999/projects",
            {
                "projects": [
                    {
                        "overview": {
                            "title": "A Project",
                            "start_date": "2023-01-01T00:00:00",
                            "url": None,
                            "url_description": None,
                            "end_date": None,
                        },
                        "description": {"text": "A description of the project."},
                        "skills": {"skills": ["Python"]},
                    },
                ],
            },
        ),
        ("/api/resumes/999/certifications", {"certifications": [{"name": "test"}]}),
    ],
)
def test_update_info_not_found(
    client_with_auth_no_resume: TestClient, endpoint: str, payload: dict
):
    """Test PUT endpoints return 404 for a non-existent resume."""
    response = client_with_auth_no_resume.put(endpoint, json=payload)
    assert response.status_code == 404
    assert response.json() == {"detail": "Resume not found"}
