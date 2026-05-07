"""Mention/attribution system: tag entries with user or team mentions."""

from __future__ import annotations

from typing import List

MENTION_KEY = "mentions"


def _normalise(mention: str) -> str:
    mention = mention.strip().lstrip("@").lower()
    if not mention:
        raise ValueError("mention must not be empty")
    return mention


def add_mention(store, entry_id: str, mention: str) -> None:
    """Add a mention (e.g. '@alice') to an entry."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"entry {entry_id!r} not found")
    name = _normalise(mention)
    mentions: List[str] = entry.metadata.get(MENTION_KEY, [])
    if name not in mentions:
        mentions.append(name)
    entry.metadata[MENTION_KEY] = mentions
    store.update(entry)


def remove_mention(store, entry_id: str, mention: str) -> None:
    """Remove a mention from an entry."""
    entry = store.get_by_id(entry_id)
    if entry is None:
        raise KeyError(f"entry {entry_id!r} not found")
    name = _normalise(mention)
    mentions: List[str] = entry.metadata.get(MENTION_KEY, [])
    entry.metadata[MENTION_KEY] = [m for m in mentions if m != name]
    store.update(entry)


def get_mentions(entry) -> List[str]:
    """Return all mentions for an entry."""
    return list(entry.metadata.get(MENTION_KEY, []))


def list_entries_with_mention(store, mention: str):
    """Return all entries that mention the given user/team."""
    name = _normalise(mention)
    return [e for e in store.all() if name in e.metadata.get(MENTION_KEY, [])]


def list_all_mentions(store) -> List[str]:
    """Return a sorted, deduplicated list of every mention across all entries."""
    seen = set()
    for entry in store.all():
        for m in entry.metadata.get(MENTION_KEY, []):
            seen.add(m)
    return sorted(seen)
