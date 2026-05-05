"""CLI helpers for the diff command."""

from typing import Optional

from reqtrace.diff import diff_entries
from reqtrace.storage import LogStore


def cmd_diff(args, store: Optional[LogStore] = None) -> None:
    """Compare two stored log entries by ID and print a human-readable diff.

    Args:
        args: Parsed CLI arguments with ``id_a`` and ``id_b`` attributes
              identifying the two log entries to compare.
        store: Optional :class:`~reqtrace.storage.LogStore` instance.  When
               *None* a default store is created automatically.
    """
    if store is None:  # pragma: no cover
        store = LogStore()

    left = store.get_by_id(args.id_a)
    right = store.get_by_id(args.id_b)

    if left is None:
        print(f"Entry not found: {args.id_a}")
        return
    if right is None:
        print(f"Entry not found: {args.id_b}")
        return

    result = diff_entries(left, right)
    print(result.summary())
