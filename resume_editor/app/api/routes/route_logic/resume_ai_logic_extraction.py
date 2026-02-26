"""Section extraction functions for resume AI logic."""

import logging

log = logging.getLogger(__name__)


def _is_top_level_section_header(line: str) -> bool:
    """Check if line is a top-level section header (# Section but not ## Subsection)."""
    stripped = line.strip()
    return stripped.startswith("# ") and not stripped.startswith("## ")


def _section_header_matches(line: str, section_header: str) -> bool:
    """Check if line matches the target section header (case insensitive)."""
    return line.strip().lower() == section_header


def _process_section_line(
    line: str,
    section_header: str,
    in_section: bool,
    captured_lines: list[str],
) -> tuple[bool, bool]:
    """Process a single line during section parsing.

    Args:
        line: The current line to process.
        section_header: The target section header to match.
        in_section: Whether we are currently inside the target section.
        captured_lines: List to append captured lines to.

    Returns:
        Tuple of (new_in_section, should_continue).

    """
    if _is_top_level_section_header(line):
        if _section_header_matches(line, section_header):
            captured_lines.append(line)
            return True, True
        if in_section:
            return False, False
    return in_section, True


def _parse_personal_section_lines(lines: list[str], section_name: str) -> list[str]:
    """Parse lines to extract personal section content."""
    section_header = f"# {section_name.lower()}"
    in_section = False
    captured_lines = []

    for line in lines:
        new_in_section, should_continue = _process_section_line(
            line, section_header, in_section, captured_lines
        )
        in_section = new_in_section
        if not should_continue:
            break
        if in_section and not _is_top_level_section_header(line):
            captured_lines.append(line)

    return captured_lines


def _rebuild_personal_section(
    lines: list[str],
    introduction: str,
    banner_found: bool,
) -> list[str]:
    """Rebuild personal section with updated banner."""
    if not banner_found:
        new_lines = list(lines)
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.extend(["## Banner", "", introduction, ""])
        return new_lines

    return lines


def _extract_raw_section(resume_content: str, section_name: str) -> str:
    """Extract the raw text of a section from resume content."""
    lines = resume_content.splitlines()
    captured_lines = _parse_personal_section_lines(lines, section_name)

    result = "\n".join(captured_lines)
    if result and not result.endswith("\n"):
        result += "\n"
    return result


def _is_section_header(line: str) -> bool:
    """Check if line is any section header."""
    stripped = line.strip()
    return stripped.startswith("## ") or stripped.startswith("# ")


def _skip_banner_content(lines: list[str], start_index: int) -> int:
    """Skip lines until next section header, return new index."""
    i = start_index
    while i < len(lines):
        if _is_section_header(lines[i]):
            return i - 1
        i += 1
    return i


def _update_banner_in_raw_personal(raw_personal: str, introduction: str | None) -> str:
    """Update the Banner subsection in a raw Personal section string."""
    if not introduction or not introduction.strip():
        return raw_personal

    stripped_intro = introduction.strip()
    lines = raw_personal.splitlines()
    new_lines = []
    banner_found = False

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.lower().startswith("## banner"):
            banner_found = True
            new_lines.extend(["## Banner", "", stripped_intro, ""])
            i = _skip_banner_content(lines, i + 1)
        else:
            new_lines.append(line)
        i += 1

    result_lines = _rebuild_personal_section(new_lines, stripped_intro, banner_found)
    result = "\n".join(result_lines)
    if result and not result.endswith("\n"):
        result += "\n"
    return result


def reconstruct_resume_with_new_introduction(
    resume_content: str,
    introduction: str | None,
) -> str:
    """Reconstruct resume with new introduction in banner."""
    _msg = "reconstruct_resume_with_new_introduction starting"
    log.debug(_msg)

    if introduction is None or not introduction.strip():
        _msg = "reconstruct_resume_with_new_introduction returning original content (no introduction)"
        log.debug(_msg)
        return resume_content

    raw_personal = _extract_raw_section(resume_content, "personal")

    if not raw_personal.strip():
        _msg = (
            "reconstruct_resume_with_new_introduction returning (no personal section)"
        )
        log.debug(_msg)
        return resume_content

    updated_personal = _update_banner_in_raw_personal(
        raw_personal,
        introduction,
    )

    result = resume_content.replace(raw_personal, updated_personal)

    _msg = "reconstruct_resume_with_new_introduction returning"
    log.debug(_msg)
    return result
