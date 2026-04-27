"""In-memory and file-based storage for request log entries."""

import json
from pathlib import Path
from typing import List, Optional

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry


class LogStore:
    """Stores and retrieves HTTP request log entries."""

    def __init__(self) -> None:
        self._entries: List[RequestLogEntry] = []

    def add(self, entry: RequestLogEntry) -> None:
        """Append a new log entry."""
        self._entries.append(entry)

    def get_by_id(self, request_id: str) -> Optional[RequestLogEntry]:
        """Find an entry by its request ID."""
        for entry in self._entries:
            if entry.request.request_id == request_id:
                return entry
        return None

    def all(self) -> List[RequestLogEntry]:
        """Return all stored entries."""
        return list(self._entries)

    def clear(self) -> None:
        """Remove all stored entries."""
        self._entries.clear()

    def save_to_file(self, path: str) -> None:
        """Persist log entries to a JSON file."""
        data = [entry.to_dict() for entry in self._entries]
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load_from_file(self, path: str) -> None:
        """Load log entries from a JSON file."""
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        for item in raw:
            req_data = item["request"]
            request = HttpRequest(
                method=req_data["method"],
                url=req_data["url"],
                headers=req_data.get("headers", {}),
                body=req_data["body"].encode("utf-8") if req_data.get("body") else None,
                query_params=req_data.get("query_params", {}),
                request_id=req_data["request_id"],
            )
            response = None
            if item.get("response"):
                res_data = item["response"]
                response = HttpResponse(
                    status_code=res_data["status_code"],
                    headers=res_data.get("headers", {}),
                    body=res_data["body"].encode("utf-8") if res_data.get("body") else None,
                    elapsed_ms=res_data.get("elapsed_ms", 0.0),
                )
            self._entries.append(RequestLogEntry(request=request, response=response))
