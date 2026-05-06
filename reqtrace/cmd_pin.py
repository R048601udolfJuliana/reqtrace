"""CLI subcommand for pinning and unpinning log entries."""

from __future__ import annotations

import argparse

from reqtrace.pin import pin_entry, unpin_entry, list_pinned
from reqtrace.highlight import method_colour, status_colour


def cmd_pin(args, store) -> None:
    action = args.pin_action

    if action == "add":
        ok = pin_entry(store, args.id)
        if ok:
            print(f"Pinned entry {args.id}")
        else:
            print(f"Entry not found: {args.id}")

    elif action == "remove":
        ok = unpin_entry(store, args.id)
        if ok:
            print(f"Unpinned entry {args.id}")
        else:
            print(f"Entry not found: {args.id}")

    elif action == "list":
        entries = list_pinned(store)
        if not entries:
            print("No pinned entries.")
            return
        for entry in entries:
            method = method_colour(entry.request.method)
            url = entry.request.url
            status = ""
            if entry.response is not None:
                status = f"  [{status_colour(entry.response.status_code)}]"
            print(f"  {entry.id[:8]}  {method} {url}{status}")


def add_pin_subcommand(subparsers) -> None:
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "pin", help="Pin or unpin log entries for quick access"
    )
    sub = parser.add_subparsers(dest="pin_action", required=True)

    add_p = sub.add_parser("add", help="Pin an entry")
    add_p.add_argument("id", help="Entry ID to pin")

    rm_p = sub.add_parser("remove", help="Unpin an entry")
    rm_p.add_argument("id", help="Entry ID to unpin")

    sub.add_parser("list", help="List all pinned entries")

    parser.set_defaults(func=cmd_pin)
