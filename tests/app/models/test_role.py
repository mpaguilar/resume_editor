from resume_editor.app.models.role import Role


def test_role_creation():
    """Test Role model creation."""
    role = Role(name="admin")
    assert role.name == "admin"
