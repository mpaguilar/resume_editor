"""Resume AI logic module - re-exports from sub-modules."""

import logging

log = logging.getLogger(__name__)

from resume_editor.app.api.routes.route_logic.resume_ai_logic_extraction import (
    _extract_raw_section,
    _update_banner_in_raw_personal,
    reconstruct_resume_with_new_introduction,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_helpers import (
    get_llm_config,
    handle_save_as_new_refinement,
    process_refined_experience_result,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_params import (
    ProcessExperienceResultParams,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_reconstruction import (
    _reconstruct_refined_resume_content,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_sse import (
    create_sse_close_message,
    create_sse_done_message,
    create_sse_error_message,
    create_sse_message,
    create_sse_progress_message,
)
from resume_editor.app.api.routes.route_logic.resume_ai_logic_streaming import (
    _build_skip_indices_from_log,
    _create_refined_role_record,
    _handle_role_refined_sse_event,
    _handle_sse_exception,
    _process_single_event,
    _stream_final_events,
    _stream_llm_events,
    experience_refinement_sse_generator,
)

# Re-exports for backward compatibility with tests
_process_sse_event = _process_single_event
_process_refined_role_event = _handle_role_refined_sse_event

__all__ = [
    "create_sse_close_message",
    "create_sse_done_message",
    "create_sse_error_message",
    "create_sse_message",
    "create_sse_progress_message",
    "experience_refinement_sse_generator",
    "get_llm_config",
    "handle_save_as_new_refinement",
    "process_refined_experience_result",
    "reconstruct_resume_with_new_introduction",
    "ProcessExperienceResultParams",
]
