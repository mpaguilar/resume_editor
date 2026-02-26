"""Main orchestration module - re-exports from sub-modules for backward compatibility."""

# Import models for backward compatibility during transition
from resume_editor.app.llm.models import GeneratedBanner
from resume_editor.app.llm.orchestration_analysis import analyze_job_description
from resume_editor.app.llm.orchestration_banner import (
    _calculate_certification_relevance,
    _calculate_education_relevance,
    _calculate_project_relevance,
    _extract_cross_section_evidence,
    _extract_section_content,
    _format_role_data_for_banner,
    _generate_introduction_from_analysis,
    _invoke_chain_and_parse,
    _invoke_banner_generation_chain,
    _parse_json_with_fix,
    _split_projects_section,
    generate_banner_from_running_log,
    generate_introduction_from_resume,
)
from resume_editor.app.llm.orchestration_client import (
    DEFAULT_LLM_TEMPERATURE,
    initialize_llm_client,
)
from resume_editor.app.llm.orchestration_refinement import (
    _create_error_context,
    _is_retryable_error,
    _log_failed_attempt,
    _truncate_for_log,
    _unwrap_exception_group,
    async_refine_experience_section,
    refine_role,
)

# Re-exports for backward compatibility with tests
_initialize_llm_client = initialize_llm_client

__all__ = [
    "_calculate_certification_relevance",
    "_calculate_education_relevance",
    "_calculate_project_relevance",
    "_create_error_context",
    "_extract_cross_section_evidence",
    "_extract_section_content",
    "_format_role_data_for_banner",
    "_generate_introduction_from_analysis",
    "_invoke_banner_generation_chain",
    "_invoke_chain_and_parse",
    "_is_retryable_error",
    "_log_failed_attempt",
    "_parse_json_with_fix",
    "_split_projects_section",
    "_truncate_for_log",
    "_unwrap_exception_group",
    "analyze_job_description",
    "async_refine_experience_section",
    "DEFAULT_LLM_TEMPERATURE",
    "generate_banner_from_running_log",
    "generate_introduction_from_resume",
    "GeneratedBanner",
    "initialize_llm_client",
    "refine_role",
]
