"""CLI subcommand: timeline — display requests in chronological order."""

from __future__ import annotations

import argparse

from reqtrace.storage import LogStore
from reqtrace.timeline import format_timeline


def cmd_timeline(
    args: argparse.Namespace,
    store: LogStore,
    out=None,
) -> None:
    """Print a timeline of logged requests."""
    import sys

    if out is None:
        out = sys.stdout

    entries = store.all()
    descending = getattr(args, "descending", False)
    print(format_timeline(entries, descending=descending), file=out)


def add_timeline_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'timeline' subcommand."""
    p: argparse.ArgumentParser = subparsers.add_parser(
        "timeline",
        help="Show requests grouped by minute in chronological order.",
    )
    p.add_argument(
        "--desc",
        dest="descending",
        action="store_true",
        default=False,
        help="Show newest buckets first.",
    )
    p.set_defaults(func=cmd_timeline)
