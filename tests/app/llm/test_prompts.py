from resume_editor.app.llm.prompts import (
    INTRO_ANALYZE_JOB_HUMAN_PROMPT,
    INTRO_ANALYZE_JOB_SYSTEM_PROMPT,
    INTRO_ANALYZE_RESUME_HUMAN_PROMPT,
    INTRO_ANALYZE_RESUME_SYSTEM_PROMPT,
    INTRO_SYNTHESIZE_INTRODUCTION_HUMAN_PROMPT,
    INTRO_SYNTHESIZE_INTRODUCTION_SYSTEM_PROMPT,
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
