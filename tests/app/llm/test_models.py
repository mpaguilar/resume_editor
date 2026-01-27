from resume_editor.app.llm.models import (
    CandidateAnalysis,
    CandidateRequirementAnalysis,
    FactualEvidence,
    GeneratedIntroduction,
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
