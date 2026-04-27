"""Export logged requests to various formats (JSON, curl commands)."""

import json
from typing import List
from reqtrace.models import RequestLogEntry


def entry_to_curl(entry: RequestLogEntry) -> str:
    """Convert a RequestLogEntry to an equivalent curl command string."""
    req = entry.request
    parts = ["curl", "-X", req.method]

    for key, value in req.headers.items():
        # Skip headers that curl sets automatically
        if key.lower() in ("host", "content-length"):
            continue
        parts.append("-H")
        parts.append(f"{key}: {value}")

    if req.body:
        escaped = req.body.replace("'", "'\\''")
        parts.append("--data")
        parts.append(f"'{escaped}'")

    parts.append(f"'{req.url}'")
    return " ".join(parts)


def entry_to_dict(entry: RequestLogEntry) -> dict:
    """Serialize a RequestLogEntry to a plain dictionary."""
    data = {
        "id": entry.id,
        "timestamp": entry.timestamp.isoformat(),
        "request": entry.request.to_dict(),
    }
    if entry.response is not None:
        data["response"] = entry.response.to_dict()
    return data


def export_json(entries: List[RequestLogEntry], indent: int = 2) -> str:
    """Serialize a list of RequestLogEntry objects to a JSON string."""
    return json.dumps([entry_to_dict(e) for e in entries], indent=indent)


def export_curl(entries: List[RequestLogEntry]) -> str:
    """Return newline-separated curl commands for each entry."""
    return "\n".join(entry_to_curl(e) for e in entries)
