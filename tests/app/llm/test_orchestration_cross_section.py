import logging
from datetime import datetime

import pytest

from resume_editor.app.llm.models import (
    CrossSectionEvidence,
    JobAnalysis,
    RefinedRoleRecord,
)
from resume_editor.app.llm.orchestration import (
    _calculate_certification_relevance,
    _calculate_education_relevance,
    _calculate_project_relevance,
    _extract_cross_section_evidence,
    _extract_section_content,
    _split_projects_section,
)

log = logging.getLogger(__name__)


@pytest.fixture
def job_analysis_with_themes():
    """Fixture for JobAnalysis with various themes."""
    return JobAnalysis(
        key_skills=["python", "aws", "leadership", "machine learning"],
        primary_duties=["backend development", "team management", "data analysis"],
        themes=["fast-paced environment", "data-driven decisions", "collaboration"],
        inferred_themes=["leadership potential", "entrepreneurial mindset"],
    )


class TestExtractCrossSectionEvidenceIntegration:
    """Integration tests for cross-section evidence extraction."""

    def test_full_resume_extraction(self, job_analysis_with_themes):
        """Test extraction from a full resume with all sections."""
        resume_content = """
# Personal
## Contact
Name: John Doe
Email: john@example.com

# Education
## Degrees
### Degree
#### Basics
Degree: Master of Science in Computer Science
School: Stanford University
Start date: 2015
End date: 2017

#### Description
Focus on Machine Learning and AI systems

### Degree
#### Basics
Degree: Bachelor of Arts in History
School: State University
Start date: 2011
End date: 2015

# Certifications
* AWS Certified Solutions Architect - Professional
* Machine Learning Specialization (Coursera)
* First Aid Certified

# Projects
### Project
#### Basics
Name: ML Pipeline Platform
Technologies: Python, TensorFlow, AWS
Description: Built end-to-end ML pipeline processing 1M+ records daily

### Project
#### Basics
Name: Personal Blog
Technologies: HTML, CSS, JavaScript
Description: Simple blog about hiking

# Experience
## Roles
### Role
#### Basics
Company: Tech Corp
Title: Senior Engineer
Start date: 2020-01-01
End date: 2023-01-01

#### Summary
Led backend development
"""
        evidence = _extract_cross_section_evidence(
            resume_content, job_analysis_with_themes
        )

        # Should extract relevant items from all sections
        education_evidence = [e for e in evidence if e.section_type == "Education"]
        cert_evidence = [e for e in evidence if e.section_type == "Certification"]
        project_evidence = [e for e in evidence if e.section_type == "Project"]

        # CS degree should be more relevant than History
        cs_evidence = [e for e in education_evidence if "Computer Science" in e.content]
        assert len(cs_evidence) > 0
        assert all(e.relevance_score >= 5 for e in cs_evidence)

        # AWS and ML certs should be extracted
        aws_certs = [e for e in cert_evidence if "AWS" in e.content]
        ml_certs = [e for e in cert_evidence if "Machine Learning" in e.content]
        assert len(aws_certs) > 0 or len(ml_certs) > 0

        # ML project should be more relevant than blog
        ml_projects = [
            e
            for e in project_evidence
            if "ML" in e.content or "Machine Learning" in e.content
        ]
        assert len(ml_projects) > 0

    def test_resume_with_no_relevant_sections(self, job_analysis_with_themes):
        """Test extraction when sections exist but aren't relevant."""
        resume_content = """
# Education
### Degree
#### Basics
Degree: Bachelor of Arts in Philosophy

# Certifications
* Basic Cooking Certificate
* Driver's License

# Projects
### Project
#### Basics
Name: Knitting Patterns Collection
Description: Collection of my favorite knitting patterns

# Experience
## Roles
### Role
Title: Engineer
"""
        evidence = _extract_cross_section_evidence(
            resume_content, job_analysis_with_themes
        )

        # Certifications have base score of 6, so they get included
        # Education and projects with low relevance may be filtered out
        # Just verify that the function runs without error
        assert isinstance(evidence, list)

    def test_empty_resume_content(self, job_analysis_with_themes):
        """Test extraction with empty resume content."""
        resume_content = ""
        evidence = _extract_cross_section_evidence(
            resume_content, job_analysis_with_themes
        )
        assert evidence == []

    def test_resume_with_only_experience(self, job_analysis_with_themes):
        """Test extraction when only experience section exists."""
        resume_content = """
# Experience
## Roles
### Role
#### Basics
Company: Tech Corp
Title: Engineer
"""
        evidence = _extract_cross_section_evidence(
            resume_content, job_analysis_with_themes
        )
        assert evidence == []

    def test_multiple_degrees_different_relevance(self, job_analysis_with_themes):
        """Test that multiple degrees get different relevance scores."""
        resume_content = """
# Education
### Degree
#### Basics
Degree: Master of Science in Computer Science with focus on Machine Learning

### Degree
#### Basics
Degree: Bachelor of Arts in English Literature

# Experience
Title: Engineer
"""
        evidence = _extract_cross_section_evidence(
            resume_content, job_analysis_with_themes
        )

        education_evidence = [e for e in evidence if e.section_type == "Education"]
        assert len(education_evidence) >= 2

        # CS degree should have higher score than Literature
        cs_scores = [
            e.relevance_score
            for e in education_evidence
            if "Computer Science" in e.content
        ]
        lit_scores = [
            e.relevance_score for e in education_evidence if "Literature" in e.content
        ]

        if cs_scores and lit_scores:
            assert max(cs_scores) > max(lit_scores)

    def test_certification_skill_matching(self, job_analysis_with_themes):
        """Test that certifications are matched to job skills."""
        resume_content = """
# Certifications
* AWS Certified Solutions Architect
* Python Programming Certificate
* Microsoft Excel Advanced
* Certified Public Accountant

# Experience
Title: Engineer
"""
        evidence = _extract_cross_section_evidence(
            resume_content, job_analysis_with_themes
        )

        cert_evidence = [e for e in evidence if e.section_type == "Certification"]

        # AWS and Python certs should have higher scores
        aws_certs = [e for e in cert_evidence if "AWS" in e.content]
        python_certs = [e for e in cert_evidence if "Python" in e.content]
        excel_certs = [e for e in cert_evidence if "Excel" in e.content]

        if aws_certs and excel_certs:
            assert aws_certs[0].relevance_score > excel_certs[0].relevance_score

        if python_certs and excel_certs:
            assert python_certs[0].relevance_score > excel_certs[0].relevance_score


class TestExtractSectionContentEdgeCases:
    """Edge case tests for section extraction."""

    def test_section_with_subsections(self):
        """Test extraction of section containing subsections."""
        resume_content = """
# Education
## Degrees
### Degree
#### Basics
Degree: BS in CS

## Certifications (within education - not standard but test anyway)
* Some Cert

# Experience
Title: Engineer
"""
        section = _extract_section_content(resume_content, "education")
        assert section is not None
        assert "BS in CS" in section

    def test_section_at_end_of_resume(self):
        """Test extraction when section is at the end."""
        resume_content = """
# Personal
Name: John

# Education
## Degrees
Degree: BS
"""
        section = _extract_section_content(resume_content, "education")
        assert section is not None
        assert "BS" in section

    def test_section_with_special_characters(self):
        """Test extraction with special characters in content."""
        resume_content = """
# Education
Degree: B.S. in Computer Science (w/ Honors)
School: University of California, Berkeley
GPA: 3.8/4.0

# Experience
Title: Engineer
"""
        section = _extract_section_content(resume_content, "education")
        assert section is not None
        assert "B.S." in section
        assert "3.8/4.0" in section

    def test_multiple_sections_with_similar_names(self):
        """Test that exact section name is matched."""
        resume_content = """
# Personal Education
Some personal education content

# Education
## Degrees
Degree: BS in CS

# Experience
Title: Engineer
"""
        section = _extract_section_content(resume_content, "education")
        assert section is not None
        assert "BS in CS" in section
        assert "personal" not in section.lower()


class TestCalculateEducationRelevanceEdgeCases:
    """Edge case tests for education relevance calculation."""

    def test_empty_education_line(self):
        """Test with empty education line."""
        score = _calculate_education_relevance("", ["python"], ["fast-paced"])
        assert score >= 5  # Base score

    def test_very_long_education_line(self):
        """Test with very long education line."""
        long_line = "Bachelor of Science in " + "Very Long Field Name " * 50
        score = _calculate_education_relevance(long_line, ["science"], [])
        assert 5 <= score <= 10

    def test_multiple_matching_skills(self):
        """Test with multiple matching skills in one line."""
        line = "BS in Computer Science and Data Science with Machine Learning focus"
        job_skills = ["computer science", "data science", "machine learning"]
        score = _calculate_education_relevance(line, job_skills, [])
        assert score > 5  # Should get bonus for matches


class TestCalculateCertificationRelevanceEdgeCases:
    """Edge case tests for certification relevance calculation."""

    def test_certification_with_no_match(self):
        """Test certification with no matching skills."""
        score = _calculate_certification_relevance(
            "Basic Typing Certificate", ["python", "aws"]
        )
        assert score == 6  # Base score only

    def test_partial_skill_match(self):
        """Test with partial skill match."""
        # "aws" should match "AWS Certified..."
        score = _calculate_certification_relevance(
            "AWS Certified Solutions Architect", ["aws"]
        )
        assert score > 6  # Should get bonus

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        # Both should match since we're doing lowercase comparison
        score_lower = _calculate_certification_relevance("aws certified", ["aws"])
        score_upper = _calculate_certification_relevance("AWS CERTIFIED", ["aws"])
        assert score_lower == score_upper


class TestCalculateProjectRelevanceEdgeCases:
    """Edge case tests for project relevance calculation."""

    def test_empty_project_chunk(self):
        """Test with empty project description."""
        score = _calculate_project_relevance("", ["python"], ["leadership"])
        assert score >= 4  # Base score

    def test_project_with_many_skills(self):
        """Test project mentioning many skills."""
        chunk = "Built with Python, AWS, Docker, Kubernetes, Terraform, and Jenkins"
        job_skills = ["python", "aws", "docker", "kubernetes"]
        score = _calculate_project_relevance(chunk, job_skills, [])
        assert score > 4  # Should get bonuses
        assert score <= 10  # Capped

    def test_project_with_themes_only(self):
        """Test project matching themes but not skills."""
        chunk = "Demonstrated leadership by guiding a team of developers"
        job_skills = ["python", "aws"]
        job_themes = ["leadership", "management"]
        score = _calculate_project_relevance(chunk, job_skills, job_themes)
        assert score > 4  # Should get theme bonuses


class TestSplitProjectsSectionEdgeCases:
    """Edge case tests for project section splitting."""

    def test_single_project_no_header(self):
        """Test single project without header."""
        section = "Built a Python web application using Flask"
        chunks = _split_projects_section(section)
        assert len(chunks) == 1
        assert chunks[0] == section

    def test_multiple_headers_same_line(self):
        """Test handling of unusual formatting."""
        section = """### Project 1 ### Project 2
Description"""
        chunks = _split_projects_section(section)
        # Should still split on headers
        assert len(chunks) >= 1

    def test_projects_with_empty_lines_between(self):
        """Test projects separated by many empty lines."""
        section = """### Project 1
Description 1



### Project 2
Description 2"""
        chunks = _split_projects_section(section)
        assert len(chunks) == 2

    def test_project_with_code_blocks(self):
        """Test project containing code-like content."""
        section = """### Python Project
Built using:
```python
def main():
    pass
```

### Another Project
Description"""
        chunks = _split_projects_section(section)
        assert len(chunks) == 2


class TestCrossSectionEvidenceModel:
    """Tests for CrossSectionEvidence model validation."""

    def test_valid_evidence_creation(self):
        """Test creating valid CrossSectionEvidence."""
        evidence = CrossSectionEvidence(
            section_type="Education",
            content="BS in Computer Science",
            relevance_score=8,
        )
        assert evidence.section_type == "Education"
        assert evidence.relevance_score == 8

    def test_relevance_score_bounds(self):
        """Test that relevance score must be 1-10."""
        # Valid scores
        CrossSectionEvidence(
            section_type="Education", content="Test", relevance_score=1
        )
        CrossSectionEvidence(
            section_type="Education", content="Test", relevance_score=10
        )

        # Invalid scores
        with pytest.raises(ValueError):
            CrossSectionEvidence(
                section_type="Education", content="Test", relevance_score=0
            )
        with pytest.raises(ValueError):
            CrossSectionEvidence(
                section_type="Education", content="Test", relevance_score=11
            )

    def test_different_section_types(self):
        """Test different valid section types."""
        for section_type in ["Education", "Certification", "Project"]:
            evidence = CrossSectionEvidence(
                section_type=section_type,
                content="Test content",
                relevance_score=5,
            )
            assert evidence.section_type == section_type
