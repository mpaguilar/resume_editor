"""SSE message helpers for resume AI logic."""

import html
import logging

log = logging.getLogger(__name__)


def create_sse_message(event: str, data: str) -> str:
    """Formats a message for Server-Sent Events (SSE).

    Args:
        event: The event name.
        data: The data to send. Can be multi-line.

    Returns:
        The formatted SSE message string.

    """
    if "\n" in data:
        data_payload = "\n".join(f"data: {line}" for line in data.splitlines())
    else:
        data_payload = f"data: {data}"

    return f"event: {event}\n{data_payload}\n\n"


def create_sse_progress_message(message: str) -> str:
    """Creates an SSE 'progress' message.

    Args:
        message: The progress message content.

    Returns:
        The formatted SSE 'progress' message.

    """
    _msg = f"create_sse_progress_message with message: {message}"
    log.debug(_msg)
    progress_html = f"<li>{html.escape(message)}</li>"
    return create_sse_message(event="progress", data=progress_html)


def create_sse_error_message(message: str, is_warning: bool = False) -> str:
    """Creates an SSE 'error' message.

    Args:
        message: The error or warning message.
        is_warning: If True, formats as a warning (yellow). Defaults to False (red).

    Returns:
        The formatted SSE 'error' message.

    """
    color_class = "text-yellow-500" if is_warning else "text-red-500"
    error_html = (
        f"<div role='alert' class='{color_class} p-2'>{html.escape(message)}</div>"
    )
    return create_sse_message(event="error", data=error_html)


def create_sse_done_message(html_content: str) -> str:
    """Creates an SSE 'done' message.

    Args:
        html_content: The final HTML content to be sent.

    Returns:
        The formatted SSE 'done' message.

    """
    return create_sse_message(event="done", data=html_content)


def create_sse_close_message() -> str:
    """Creates an SSE 'close' message.

    Returns:
        The formatted SSE 'close' message.

    """
    return create_sse_message(event="close", data="stream complete")
