"""Per-entry notes/annotations for request log entries."""

from reqtrace.storage import LogStore

NOTES_KEY = "__notes__"


def add_note(store: LogStore, entry_id: str, note: str) -> None:
    """Append a note to the entry's metadata."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry not found: {entry_id}")
    note = note.strip()
    if not note:
        raise ValueError("Note must not be empty")
    existing = entry.metadata.get(NOTES_KEY, [])
    if isinstance(existing, str):
        existing = [existing]
    existing.append(note)
    entry.metadata[NOTES_KEY] = existing
    store.update(entry)


def get_notes(store: LogStore, entry_id: str) -> list[str]:
    """Return all notes attached to an entry."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry not found: {entry_id}")
    raw = entry.metadata.get(NOTES_KEY, [])
    if isinstance(raw, str):
        return [raw]
    return list(raw)


def clear_notes(store: LogStore, entry_id: str) -> None:
    """Remove all notes from an entry."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"Entry not found: {entry_id}")
    entry.metadata.pop(NOTES_KEY, None)
    store.update(entry)


def list_entries_with_notes(store: LogStore) -> list:
    """Return all entries that have at least one note."""
    return [
        e for e in store.all()
        if e.metadata.get(NOTES_KEY)
    ]
