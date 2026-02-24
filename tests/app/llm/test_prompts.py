from resume_editor.app.llm.prompts import (
    BANNER_GENERATION_HUMAN_PROMPT,
    BANNER_GENERATION_SYSTEM_PROMPT,
    INTRO_ANALYZE_JOB_HUMAN_PROMPT,
    INTRO_ANALYZE_JOB_SYSTEM_PROMPT,
    INTRO_ANALYZE_RESUME_HUMAN_PROMPT,
    INTRO_ANALYZE_RESUME_SYSTEM_PROMPT,
    INTRO_SYNTHESIZE_INTRODUCTION_HUMAN_PROMPT,
    INTRO_SYNTHESIZE_INTRODUCTION_SYSTEM_PROMPT,
    JOB_ANALYSIS_SYSTEM_PROMPT,
    ROLE_REFINE_SYSTEM_PROMPT,
)


def test_role_refine_system_prompt_enforces_factual_summary():
    """
    Tests that the ROLE_REFINE_SYSTEM_PROMPT enforces factual summaries.

    It should not prompt the LLM to invent content by incorporating keywords
    from the job analysis into the summary. Instead, it should explicitly
    state that the summary must be based only on the original role content.
    """
    # This is the problematic phrase that encourages hallucination
    problematic_phrase = (
        "incorporate high-level keywords and themes from the `job_analysis`"
    )

    # This is the new, stricter instruction that should be present
    strict_instruction = (
        "MUST be based *only* on the content of the original 'role' object"
    )

    assert problematic_phrase not in ROLE_REFINE_SYSTEM_PROMPT
    assert strict_instruction in ROLE_REFINE_SYSTEM_PROMPT


def test_new_introduction_prompts_exist_and_are_not_empty():
    """Tests that the new introduction-related prompts are not empty."""
    prompts = {
        "INTRO_ANALYZE_JOB_SYSTEM_PROMPT": INTRO_ANALYZE_JOB_SYSTEM_PROMPT,
        "INTRO_ANALYZE_JOB_HUMAN_PROMPT": INTRO_ANALYZE_JOB_HUMAN_PROMPT,
        "INTRO_ANALYZE_RESUME_SYSTEM_PROMPT": INTRO_ANALYZE_RESUME_SYSTEM_PROMPT,
        "INTRO_ANALYZE_RESUME_HUMAN_PROMPT": INTRO_ANALYZE_RESUME_HUMAN_PROMPT,
        "INTRO_SYNTHESIZE_INTRODUCTION_SYSTEM_PROMPT": INTRO_SYNTHESIZE_INTRODUCTION_SYSTEM_PROMPT,
        "INTRO_SYNTHESIZE_INTRODUCTION_HUMAN_PROMPT": INTRO_SYNTHESIZE_INTRODUCTION_HUMAN_PROMPT,
    }

    for name, prompt in prompts.items():
        assert prompt is not None, f"{name} should not be None"
        assert isinstance(prompt, str), f"{name} should be a string"
        assert len(prompt.strip()) > 0, f"{name} should not be empty"


def test_intro_analyze_resume_prompt_is_factual_and_structured():
    """Tests that INTRO_ANALYZE_RESUME_SYSTEM_PROMPT is for factual, structured evidence."""
    prompt = INTRO_ANALYZE_RESUME_SYSTEM_PROMPT
    assert "factual evidence" in prompt.lower()
    assert "source_section" in prompt.lower()
    assert "do not invent or imply" in prompt.lower()
    assert "empty `evidence` list" in prompt.lower()
    assert "relevance" in prompt
    assert "'Personal'" in prompt
    assert "'direct' (matches primary duty)" in prompt
    assert "'indirect' (related but not core)" in prompt


def test_intro_synthesize_prompt_is_exclusive_and_prioritized():
    """Tests that INTRO_SYNTHESIZE_INTRODUCTION_SYSTEM_PROMPT is for an exclusive, prioritized list."""
    prompt = INTRO_SYNTHESIZE_INTRODUCTION_SYSTEM_PROMPT
    assert "exclusively factual" in prompt.lower()
    assert "verifiable from the `evidence` fields" in prompt
    assert "no exaggeration, embellishment, or superlatives" in prompt.lower()
    assert "strict prioritization" in prompt.lower()
    # Check prioritization order
    assert "1. work experience (direct relevance)" in prompt.lower()
    assert "2. work experience (indirect relevance)" in prompt.lower()
    assert "3. certification" in prompt.lower()
    assert "4. project" in prompt.lower()
    assert "5. education" in prompt.lower()
    assert "6. personal" in prompt.lower()


def test_intro_analyze_resume_prompt_has_original_banner():
    """Tests that INTRO_ANALYZE_RESUME_HUMAN_PROMPT includes original_banner placeholder."""
    assert "{original_banner}" in INTRO_ANALYZE_RESUME_HUMAN_PROMPT


def test_job_analysis_prompt_has_theme_inference():
    """Tests that JOB_ANALYSIS_SYSTEM_PROMPT includes theme inference instruction."""
    assert "Infer Implicit Themes" in JOB_ANALYSIS_SYSTEM_PROMPT
    assert (
        "inferred_themes" in JOB_ANALYSIS_SYSTEM_PROMPT.lower()
        or "implicit themes" in JOB_ANALYSIS_SYSTEM_PROMPT.lower()
    )


def test_banner_generation_system_prompt_exists_and_not_empty():
    """Tests that BANNER_GENERATION_SYSTEM_PROMPT exists and is not empty."""
    assert BANNER_GENERATION_SYSTEM_PROMPT is not None
    assert isinstance(BANNER_GENERATION_SYSTEM_PROMPT, str)
    assert len(BANNER_GENERATION_SYSTEM_PROMPT.strip()) > 0


def test_banner_generation_system_prompt_has_required_elements():
    """Tests that BANNER_GENERATION_SYSTEM_PROMPT contains all required instructions."""
    prompt = BANNER_GENERATION_SYSTEM_PROMPT
    # Key requirements from the implementation plan
    assert "100% Factual Accuracy" in prompt
    assert "Role-Centric Focus" in prompt
    assert "Semantic Grouping" in prompt
    assert "Bold Prefix Format" in prompt
    assert "**Category:**" in prompt
    assert "Company Associations" in prompt
    assert "parenthetical company lists" in prompt.lower()
    assert "Job-Relevant Prioritization" in prompt
    assert "Honesty Constraint" in prompt
    assert "Education Conditional" in prompt
    assert "relevance_score >= 8" in prompt
    # Company names must be italicized
    assert "ITALICIZED" in prompt or "italicized" in prompt.lower()
    assert "*Company A*" in prompt or "*Company" in prompt


def test_banner_generation_human_prompt_exists_and_has_placeholders():
    """Tests that BANNER_GENERATION_HUMAN_PROMPT exists and has required placeholders."""
    assert BANNER_GENERATION_HUMAN_PROMPT is not None
    assert isinstance(BANNER_GENERATION_HUMAN_PROMPT, str)
    assert "{job_analysis_json}" in BANNER_GENERATION_HUMAN_PROMPT
    assert "{refined_roles_json}" in BANNER_GENERATION_HUMAN_PROMPT
    assert "{cross_section_evidence_json}" in BANNER_GENERATION_HUMAN_PROMPT
    assert "{original_banner}" in BANNER_GENERATION_HUMAN_PROMPT


def test_banner_generation_prompts_are_different():
    """Tests that system and human prompts are different."""
    assert BANNER_GENERATION_SYSTEM_PROMPT != BANNER_GENERATION_HUMAN_PROMPT
