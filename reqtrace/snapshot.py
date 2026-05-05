"""Snapshot support: save and restore named snapshots of the log store."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reqtrace.storage import LogStore

from reqtrace.exporter import entry_to_dict
from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def save_snapshot(store: "LogStore", name: str) -> dict:
    """Serialise all entries in *store* into a snapshot dict keyed by *name*."""
    entries = [entry_to_dict(e) for e in store.all()]
    return {"name": name, "entries": entries}


def _entry_from_dict(data: dict) -> RequestLogEntry:
    req_d = data["request"]
    req = HttpRequest(
        method=req_d["method"],
        url=req_d["url"],
        headers=req_d.get("headers", {}),
        body=req_d.get("body"),
    )
    resp = None
    if data.get("response"):
        resp_d = data["response"]
        resp = HttpResponse(
            status_code=resp_d["status_code"],
            headers=resp_d.get("headers", {}),
            body=resp_d.get("body"),
        )
    entry = RequestLogEntry(request=req, response=resp)
    entry.id = data["id"]
    entry.timestamp = data["timestamp"]
    if data.get("tags"):
        entry.tags = list(data["tags"])
    if data.get("notes"):
        entry.notes = list(data["notes"])
    return entry


def load_snapshot(store: "LogStore", snapshot: dict) -> int:
    """Load entries from *snapshot* into *store*. Returns number of entries added."""
    if "entries" not in snapshot:
        raise SnapshotError("Invalid snapshot: missing 'entries' key")
    count = 0
    for raw in snapshot["entries"]:
        entry = _entry_from_dict(raw)
        store.add(entry)
        count += 1
    return count


def snapshot_to_json(snapshot: dict) -> str:
    """Serialise a snapshot dict to a JSON string."""
    return json.dumps(snapshot, indent=2)


def snapshot_from_json(text: str) -> dict:
    """Deserialise a snapshot dict from a JSON string."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise SnapshotError(f"Invalid JSON: {exc}") from exc
    return data
