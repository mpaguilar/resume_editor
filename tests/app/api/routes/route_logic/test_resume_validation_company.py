"""Tests for resume validation with company and notes fields."""

import pytest

from resume_editor.app.api.routes.route_logic.resume_validation import (
    MAX_COMPANY_LENGTH,
    MAX_NOTES_LENGTH,
    validate_company_and_notes,
    validate_refinement_form,
)


class TestValidateCompanyAndNotes:
    def test_valid_company_and_notes(self):
        result = validate_company_and_notes("Acme Corp", "Some notes")
        assert result.is_valid is True
        assert result.errors == {}

    def test_valid_none_values(self):
        result = validate_company_and_notes(None, None)
        assert result.is_valid is True
        assert result.errors == {}

    def test_valid_empty_strings(self):
        result = validate_company_and_notes("", "")
        assert result.is_valid is True
        assert result.errors == {}

    def test_company_at_max_length(self):
        company = "A" * MAX_COMPANY_LENGTH
        result = validate_company_and_notes(company, None)
        assert result.is_valid is True
        assert result.errors == {}

    def test_company_exceeds_max_length(self):
        company = "A" * (MAX_COMPANY_LENGTH + 1)
        result = validate_company_and_notes(company, None)
        assert result.is_valid is False
        assert "company" in result.errors
        assert f"{MAX_COMPANY_LENGTH}" in result.errors["company"]

    def test_notes_at_max_length(self):
        notes = "A" * MAX_NOTES_LENGTH
        result = validate_company_and_notes(None, notes)
        assert result.is_valid is True
        assert result.errors == {}

    def test_notes_exceeds_max_length(self):
        notes = "A" * (MAX_NOTES_LENGTH + 1)
        result = validate_company_and_notes(None, notes)
        assert result.is_valid is False
        assert "notes" in result.errors
        assert f"{MAX_NOTES_LENGTH}" in result.errors["notes"]

    def test_both_fields_invalid(self):
        company = "A" * (MAX_COMPANY_LENGTH + 1)
        notes = "A" * (MAX_NOTES_LENGTH + 1)
        result = validate_company_and_notes(company, notes)
        assert result.is_valid is False
        assert "company" in result.errors
        assert "notes" in result.errors

    def test_company_with_special_characters(self):
        company = "Acme Corp. & Sons, LLC (USA)"
        result = validate_company_and_notes(company, None)
        assert result.is_valid is True


class TestValidateRefinementForm:
    def test_valid_form(self):
        result = validate_refinement_form(
            job_description="Software Engineer position",
            company="Acme Corp",
            notes="Some notes",
        )
        assert result.is_valid is True
        assert result.errors == {}

    def test_missing_job_description(self):
        result = validate_refinement_form(
            job_description=None,
            company="Acme Corp",
            notes=None,
        )
        assert result.is_valid is False
        assert "job_description" in result.errors

    def test_empty_job_description(self):
        result = validate_refinement_form(
            job_description="   ",
            company="Acme Corp",
            notes=None,
        )
        assert result.is_valid is False
        assert "job_description" in result.errors

    def test_invalid_company_and_notes(self):
        result = validate_refinement_form(
            job_description="Valid job description",
            company="A" * (MAX_COMPANY_LENGTH + 1),
            notes="A" * (MAX_NOTES_LENGTH + 1),
        )
        assert result.is_valid is False
        assert "company" in result.errors
        assert "notes" in result.errors
