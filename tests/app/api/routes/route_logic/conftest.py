import pytest

from resume_editor.app.models.resume_model import (
    Resume as DatabaseResume,
    ResumeData,
)
from resume_editor.app.models.user import User, UserData

VALID_RESUME_TWO_ROLES = """# Personal

## Contact Information

Name: Test Person

# Education

## Degrees

### Degree

School: A School

# Certifications

## Certification

Name: A Cert

# Experience

## Roles

### Role

#### Basics

Company: A Company
Title: A Role
Start date: 01/2024

### Role

#### Basics

Company: B Company
Title: B Role
Start date: 01/2023

## Projects

### Project

#### Overview

Title: A Cool Project
#### Description

A project description.
"""


@pytest.fixture
def test_user():
    """Fixture for a test user."""
    user = User(
        data=UserData(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password",
            id_=1,
        )
    )
    return user


@pytest.fixture
def test_resume(test_user):
    """Fixture for a test resume."""
    resume_data = ResumeData(
        user_id=test_user.id,
        name="Test Resume",
        content=VALID_RESUME_TWO_ROLES,
    )
    resume = DatabaseResume(data=resume_data)
    resume.id = 1
    return resume


class NthAsyncItem:
    """Helper to await until the nth item of an async iterator is produced."""

    def __init__(self, async_iterator, n):
        self.async_iterator = async_iterator
        self.n = n
        self.items = []

    def __await__(self):
        return self.get_items().__await__()

    async def get_items(self):
        async for item in self.async_iterator:
            self.items.append(item)
            if len(self.items) == self.n:
                break
        return self.items

    @classmethod
    def of(cls, async_iterator, n):
        return cls(async_iterator, n)
