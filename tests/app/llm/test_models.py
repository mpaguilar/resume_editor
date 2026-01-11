from resume_editor.app.llm.models import (
    CandidateAnalysis,
    GeneratedIntroduction,
    JobKeyRequirements,
    SkillAssessment,
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
    """Tests the instantiation of the CandidateAnalysis model."""
    data = {
        "skill_summary": {
            "Python": {
                "assessment": "extensive experience",
                "source": ["Work Experience"],
            },
        }
    }
    instance = CandidateAnalysis(**data)
    assert instance.model_dump() == data


def test_generated_introduction_instantiation():
    """Tests the instantiation of the GeneratedIntroduction model."""
    data = {"strengths": ["This is a test strength."]}
    instance = GeneratedIntroduction(**data)
    assert instance.model_dump() == data


def test_skill_assessment_instantiation():
    """Tests the instantiation of the SkillAssessment model."""
    data = {
        "assessment": "extensive experience",
        "source": ["Work Experience"],
    }
    instance = SkillAssessment(**data)
    assert instance.model_dump() == data
