"""Badge generation for request log entries.

Produces small text-based status badges (similar to shields.io style labels)
that can be embedded in reports or printed to the terminal.
"""

from __future__ import annotations

from typing import Optional

from reqtrace.models import RequestLogEntry

# ANSI colour codes
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_BLUE = "\033[34m"
_CYAN = "\033[36m"
_RESET = "\033[0m"
_BOLD = "\033[1m"


def _colour(text: str, code: str, *, use_colour: bool = True) -> str:
    if not use_colour:
        return text
    return f"{code}{text}{_RESET}"


def status_badge(entry: RequestLogEntry, *, use_colour: bool = True) -> str:
    """Return a badge string representing the HTTP response status."""
    if entry.response is None:
        label = "NO RESPONSE"
        return _colour(f"[{label}]", _YELLOW, use_colour=use_colour)
    code = entry.response.status_code
    if 200 <= code < 300:
        colour = _GREEN
    elif 300 <= code < 400:
        colour = _CYAN
    elif 400 <= code < 500:
        colour = _YELLOW
    else:
        colour = _RED
    return _colour(f"[{code}]", colour, use_colour=use_colour)


def method_badge(entry: RequestLogEntry, *, use_colour: bool = True) -> str:
    """Return a badge string for the HTTP method."""
    method = entry.request.method.upper()
    colour_map = {
        "GET": _GREEN,
        "POST": _CYAN,
        "PUT": _BLUE,
        "PATCH": _BLUE,
        "DELETE": _RED,
    }
    colour = colour_map.get(method, _YELLOW)
    return _colour(f"[{method}]", colour, use_colour=use_colour)


def tag_badge(entry: RequestLogEntry, *, use_colour: bool = True) -> str:
    """Return a badge listing tags attached to the entry, or empty string."""
    tags: list[str] = entry.metadata.get("tags", [])
    if not tags:
        return ""
    joined = ", ".join(sorted(tags))
    return _colour(f"[tags: {joined}]", _BLUE, use_colour=use_colour)


def format_badge_line(
    entry: RequestLogEntry,
    *,
    use_colour: bool = True,
) -> str:
    """Return a single formatted line with method, status, url, and tags."""
    parts = [
        method_badge(entry, use_colour=use_colour),
        status_badge(entry, use_colour=use_colour),
        entry.request.url,
    ]
    tag_b = tag_badge(entry, use_colour=use_colour)
    if tag_b:
        parts.append(tag_b)
    return "  ".join(parts)
