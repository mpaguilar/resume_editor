import pytest

from resume_editor.app.llm.models import (
    BannerBullet,
    CandidateAnalysis,
    CandidateRequirementAnalysis,
    CrossSectionEvidence,
    FactualEvidence,
    GeneratedBanner,
    GeneratedIntroduction,
    JobAnalysis,
    JobKeyRequirements,
)


def test_job_key_requirements_instantiation():
    """Tests the instantiation of the JobKeyRequirements model."""
    data = {
        "key_skills": ["Python", "FastAPI"],
        "candidate_priorities": ["Focus on backend development and API design."],
    }
    instance = JobKeyRequirements(**data)
    assert instance.model_dump() == data


def test_candidate_analysis_instantiation():
    """Tests the instantiation of the updated CandidateAnalysis model and its nested models."""
    data = {
        "analysis": [
            {
                "job_requirement": "Python",
                "evidence": [
                    {
                        "evidence": "Developed API with Python and FastAPI.",
                        "source_section": "Work Experience",
                        "relevance": "direct",
                    },
                    {
                        "evidence": "Completed a personal project using Python.",
                        "source_section": "Project",
                        "relevance": None,
                    },
                ],
            },
            {
                "job_requirement": "Management",
                "evidence": [
                    {
                        "evidence": "Led a team of 3 junior developers.",
                        "source_section": "Work Experience",
                        "relevance": "indirect",
                    }
                ],
            },
            {
                "job_requirement": "Communication",
                "evidence": [
                    {
                        "evidence": "Strong communicator and team player.",
                        "source_section": "Personal",
                        "relevance": None,
                    }
                ],
            },
            {"job_requirement": "Rust", "evidence": []},
        ]
    }
    instance = CandidateAnalysis(**data)
    assert instance.model_dump() == data
    assert isinstance(instance.analysis[0], CandidateRequirementAnalysis)
    assert isinstance(instance.analysis[0].evidence[0], FactualEvidence)


def test_generated_introduction_instantiation():
    """Tests the instantiation of the GeneratedIntroduction model."""
    data = {"strengths": ["This is a test strength."]}
    instance = GeneratedIntroduction(**data)
    assert instance.model_dump() == data


def test_job_analysis_with_inferred_themes():
    """Tests the JobAnalysis model with the inferred_themes field."""
    data = {
        "key_skills": ["Python", "FastAPI"],
        "primary_duties": ["Backend development", "API design"],
        "themes": ["fast-paced environment", "data-driven"],
        "inferred_themes": ["leadership potential", "collaborative culture"],
    }
    instance = JobAnalysis(**data)
    assert instance.model_dump() == data
    assert instance.inferred_themes == ["leadership potential", "collaborative culture"]


def test_job_analysis_default_inferred_themes():
    """Tests that JobAnalysis defaults to empty list for inferred_themes."""
    data = {
        "key_skills": ["Python"],
        "primary_duties": ["Development"],
        "themes": ["fast-paced"],
    }
    instance = JobAnalysis(**data)
    assert instance.inferred_themes == []


def test_cross_section_evidence_instantiation():
    """Tests the instantiation of the CrossSectionEvidence model."""
    data = {
        "section_type": "Education",
        "content": "Master's in Computer Science with focus on AI",
        "relevance_score": 9,
    }
    instance = CrossSectionEvidence(**data)
    assert instance.model_dump() == data
    assert instance.section_type == "Education"
    assert instance.relevance_score == 9


def test_cross_section_evidence_relevance_bounds():
    """Tests that CrossSectionEvidence enforces relevance score bounds."""
    # Test minimum bound
    with pytest.raises(ValueError):
        CrossSectionEvidence(
            section_type="Certification",
            content="AWS Certified",
            relevance_score=0,
        )
    # Test maximum bound
    with pytest.raises(ValueError):
        CrossSectionEvidence(
            section_type="Project",
            content="Machine learning project",
            relevance_score=11,
        )


def test_banner_bullet_instantiation():
    """Tests the instantiation of the BannerBullet model."""
    data = {
        "category": "Cloud Platforms",
        "description": "Extensive experience with AWS (Company A, Company B) and Azure (Company C)",
    }
    instance = BannerBullet(**data)
    assert instance.model_dump() == data
    assert instance.category == "Cloud Platforms"


def test_generated_banner_instantiation():
    """Tests the instantiation of the GeneratedBanner model."""
    data = {
        "bullets": [
            {
                "category": "Leadership",
                "description": "Led teams of 5-10 engineers (Company A, Company B)",
            },
            {
                "category": "Backend Development",
                "description": "Expert in Python and FastAPI (Company C)",
            },
        ],
        "education_bullet": {
            "category": "Education",
            "description": "Master's in Computer Science directly relevant to ML role",
        },
    }
    instance = GeneratedBanner(**data)
    assert len(instance.bullets) == 2
    assert instance.education_bullet is not None
    assert instance.education_bullet.category == "Education"


def test_generated_banner_default_empty():
    """Tests that GeneratedBanner defaults to empty bullets and no education."""
    instance = GeneratedBanner()
    assert instance.bullets == []
    assert instance.education_bullet is None


def test_generated_banner_without_education():
    """Tests GeneratedBanner without education bullet."""
    data = {
        "bullets": [
            {"category": "DevOps", "description": "CI/CD expertise (Company X)"},
        ],
    }
    instance = GeneratedBanner(**data)
    assert len(instance.bullets) == 1
    assert instance.education_bullet is None
