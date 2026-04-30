"""Syntax-style highlighting helpers for reqtrace CLI output."""

from typing import Optional

# ANSI colour codes
_RESET  = "\033[0m"
_BOLD   = "\033[1m"
_RED    = "\033[31m"
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_CYAN   = "\033[36m"
_GREY   = "\033[90m"


def _c(code: str, text: str, enabled: bool) -> str:
    return f"{code}{text}{_RESET}" if enabled else text


def method_colour(method: str, enabled: bool = True) -> str:
    """Return the HTTP method string wrapped in an appropriate colour."""
    method = method.upper()
    mapping = {
        "GET":    _GREEN,
        "POST":   _CYAN,
        "PUT":    _YELLOW,
        "PATCH":  _YELLOW,
        "DELETE": _RED,
        "HEAD":   _GREY,
        "OPTIONS": _GREY,
    }
    code = mapping.get(method, _RESET)
    return _c(code, method, enabled)


def status_colour(status: Optional[int], enabled: bool = True) -> str:
    """Return the HTTP status code wrapped in an appropriate colour."""
    if status is None:
        return _c(_GREY, "N/A", enabled)
    text = str(status)
    if status < 300:
        code = _GREEN
    elif status < 400:
        code = _CYAN
    elif status < 500:
        code = _YELLOW
    else:
        code = _RED
    return _c(code, text, enabled)


def url_highlight(url: str, enabled: bool = True) -> str:
    """Highlight a URL: bold scheme+host, normal path."""
    if not enabled:
        return url
    if "://" in url:
        scheme_end = url.index("://") + 3
        slash_after = url.find("/", scheme_end)
        if slash_after == -1:
            host_part = url
            path_part = ""
        else:
            host_part = url[:slash_after]
            path_part = url[slash_after:]
        return f"{_BOLD}{host_part}{_RESET}{path_part}"
    return url


def header_highlight(name: str, value: str, enabled: bool = True) -> str:
    """Format a single header line with the name highlighted."""
    if not enabled:
        return f"{name}: {value}"
    return f"{_CYAN}{name}{_RESET}: {value}"


def bold(text: str, enabled: bool = True) -> str:
    return _c(_BOLD, text, enabled)
