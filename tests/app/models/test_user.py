import pytest

from resume_editor.app.models.user import User, UserData

# Valid default data for tests
VALID_USERNAME = "testuser"
VALID_EMAIL = "test@example.com"
VALID_PASSWORD = "hashed_password"


def test_user_creation_successful():
    """Test successful creation, including stripping of whitespace from fields."""
    user_data = UserData(
        username=f" {VALID_USERNAME} ",
        email=f" {VALID_EMAIL} ",
        hashed_password=f" {VALID_PASSWORD} ",
        is_active=True,
        attributes={"key": "value"},
    )
    user = User(data=user_data)
    assert user.username == VALID_USERNAME
    assert user.email == VALID_EMAIL
    assert user.hashed_password == VALID_PASSWORD
    assert user.is_active is True
    assert user.attributes == {"key": "value"}


@pytest.mark.parametrize(
    "username, error_msg",
    [
        (123, "Username must be a string"),
        ("", "Username cannot be empty"),
        ("   ", "Username cannot be empty"),
    ],
)
def test_validate_username_failures(username, error_msg):
    """Test validate_username raises ValueError for invalid inputs."""
    with pytest.raises(ValueError, match=error_msg):
        user_data = UserData(
            username=username,
            email=VALID_EMAIL,
            hashed_password=VALID_PASSWORD,
        )
        User(data=user_data)


@pytest.mark.parametrize(
    "email, error_msg",
    [
        (123, "Email must be a string"),
        ("", "Email cannot be empty"),
        ("   ", "Email cannot be empty"),
    ],
)
def test_validate_email_failures(email, error_msg):
    """Test validate_email raises ValueError for invalid inputs."""
    with pytest.raises(ValueError, match=error_msg):
        user_data = UserData(
            username=VALID_USERNAME,
            email=email,
            hashed_password=VALID_PASSWORD,
        )
        User(data=user_data)


@pytest.mark.parametrize(
    "password, error_msg",
    [
        (123, "Hashed password must be a string"),
        ("", "Hashed password cannot be empty"),
        ("   ", "Hashed password cannot be empty"),
    ],
)
def test_validate_hashed_password_failures(password, error_msg):
    """Test validate_hashed_password raises ValueError for invalid inputs."""
    with pytest.raises(ValueError, match=error_msg):
        user_data = UserData(
            username=VALID_USERNAME,
            email=VALID_EMAIL,
            hashed_password=password,
        )
        User(data=user_data)


def test_validate_is_active_failure():
    """Test validate_is_active raises ValueError for invalid input."""
    with pytest.raises(ValueError, match="is_active must be a boolean"):
        user_data = UserData(
            username=VALID_USERNAME,
            email=VALID_EMAIL,
            hashed_password=VALID_PASSWORD,
            is_active="not_a_bool",
        )
        User(data=user_data)


def test_user_creation_with_attributes():
    """Test User model creation with attributes."""
    attrs = {"key": "value"}
    user_data = UserData(
        username=VALID_USERNAME,
        email=VALID_EMAIL,
        hashed_password=VALID_PASSWORD,
        attributes=attrs,
    )
    user = User(data=user_data)
    assert user.attributes == attrs


def test_user_creation_without_attributes():
    """Test User model creation without attributes, should default to None."""
    user_data = UserData(
        username=VALID_USERNAME,
        email=VALID_EMAIL,
        hashed_password=VALID_PASSWORD,
    )
    user = User(data=user_data)
    assert user.attributes is None


def test_validate_attributes_with_invalid_type():
    """Test that validate_attributes raises ValueError for non-dict types."""
    with pytest.raises(ValueError, match="Attributes must be a dictionary"):
        user_data = UserData(
            username=VALID_USERNAME,
            email=VALID_EMAIL,
            hashed_password=VALID_PASSWORD,
            attributes=["not", "a", "dict"],
        )
        User(data=user_data)
