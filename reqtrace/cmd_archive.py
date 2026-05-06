"""CLI subcommand for archiving and unarchiving log entries."""

from __future__ import annotations

import argparse

from reqtrace.archive import (
    archive_entry,
    unarchive_entry,
    is_archived,
    list_archived,
    list_active,
    purge_archived,
)


def cmd_archive(args: argparse.Namespace, store) -> None:
    action = args.archive_action

    if action == "add":
        ok = archive_entry(store, args.id)
        if ok:
            print(f"Entry {args.id} archived.")
        else:
            print(f"Entry {args.id} not found.")

    elif action == "remove":
        ok = unarchive_entry(store, args.id)
        if ok:
            print(f"Entry {args.id} unarchived.")
        else:
            print(f"Entry {args.id} not found.")

    elif action == "list":
        show = args.show if hasattr(args, "show") else "archived"
        entries = list_active(store) if show == "active" else list_archived(store)
        if not entries:
            print("No entries found.")
        else:
            for e in entries:
                status = "[archived]" if is_archived(e) else "[active]"
                print(f"{e.id}  {status}  {e.request.method}  {e.request.url}")

    elif action == "purge":
        count = purge_archived(store)
        print(f"Purged {count} archived entry/entries.")


def add_archive_subcommand(subparsers) -> None:
    p = subparsers.add_parser("archive", help="Archive or unarchive log entries")
    sub = p.add_subparsers(dest="archive_action", required=True)

    add_p = sub.add_parser("add", help="Archive an entry")
    add_p.add_argument("id", help="Entry ID to archive")

    rm_p = sub.add_parser("remove", help="Unarchive an entry")
    rm_p.add_argument("id", help="Entry ID to unarchive")

    ls_p = sub.add_parser("list", help="List archived or active entries")
    ls_p.add_argument(
        "--show",
        choices=["archived", "active"],
        default="archived",
        help="Which entries to show (default: archived)",
    )

    sub.add_parser("purge", help="Permanently delete all archived entries")

    p.set_defaults(func=cmd_archive)
