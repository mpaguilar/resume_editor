from resume_editor.app.llm.prompts import ROLE_REFINE_SYSTEM_PROMPT


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
