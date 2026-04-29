"""CLI subcommands for managing bookmarked log entries."""

from __future__ import annotations

import argparse

from reqtrace.bookmark import bookmark_entry, unbookmark_entry, list_bookmarks
from reqtrace.storage import LogStore


def cmd_bookmark(args: argparse.Namespace, store: LogStore) -> None:
    """Dispatch bookmark subcommands."""
    if args.bookmark_cmd == "add":
        try:
            entry = bookmark_entry(store, args.id)
            print(f"Bookmarked entry {entry.id}")
        except KeyError as exc:
            print(f"Error: {exc}")

    elif args.bookmark_cmd == "remove":
        try:
            entry = unbookmark_entry(store, args.id)
            print(f"Removed bookmark from entry {entry.id}")
        except KeyError as exc:
            print(f"Error: {exc}")

    elif args.bookmark_cmd == "list":
        entries = list_bookmarks(store)
        if not entries:
            print("No bookmarked entries.")
        else:
            for e in entries:
                ts = e.timestamp or ""
                print(f"[{e.id}] {ts}  {e.request.method} {e.request.url}")


def add_bookmark_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the 'bookmark' command group onto an existing subparsers object."""
    bk_parser = subparsers.add_parser("bookmark", help="Manage bookmarked entries")
    bk_sub = bk_parser.add_subparsers(dest="bookmark_cmd", required=True)

    add_p = bk_sub.add_parser("add", help="Bookmark an entry")
    add_p.add_argument("id", help="Entry ID to bookmark")

    rm_p = bk_sub.add_parser("remove", help="Remove bookmark from an entry")
    rm_p.add_argument("id", help="Entry ID to un-bookmark")

    bk_sub.add_parser("list", help="List all bookmarked entries")

    bk_parser.set_defaults(func=cmd_bookmark)
