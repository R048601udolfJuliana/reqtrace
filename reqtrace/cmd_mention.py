"""CLI sub-command for managing entry mentions."""

from __future__ import annotations

import argparse

from reqtrace import mention as _mention


def cmd_mention(args: argparse.Namespace, store) -> None:
    action = args.mention_action

    if action == "add":
        try:
            _mention.add_mention(store, args.id, args.name)
            print(f"Mentioned @{args.name.lstrip('@').lower()} on entry {args.id}.")
        except KeyError as exc:
            print(str(exc))

    elif action == "remove":
        try:
            _mention.remove_mention(store, args.id, args.name)
            print(f"Removed mention @{args.name.lstrip('@').lower()} from entry {args.id}.")
        except KeyError as exc:
            print(str(exc))

    elif action == "list":
        try:
            entry = store.get_by_id(args.id)
            if entry is None:
                print(f"Entry {args.id!r} not found.")
                return
            mentions = _mention.get_mentions(entry)
            if mentions:
                for m in mentions:
                    print(f"  @{m}")
            else:
                print("No mentions.")
        except KeyError as exc:
            print(str(exc))

    elif action == "search":
        entries = _mention.list_entries_with_mention(store, args.name)
        if not entries:
            print(f"No entries mention @{args.name.lstrip('@').lower()}.")
        else:
            for e in entries:
                print(f"  {e.id}  {e.request.method}  {e.request.url}")

    elif action == "all":
        names = _mention.list_all_mentions(store)
        if not names:
            print("No mentions recorded.")
        else:
            for n in names:
                print(f"  @{n}")


def add_mention_subcommand(subparsers) -> None:
    p = subparsers.add_parser("mention", help="Manage entry mentions")
    sub = p.add_subparsers(dest="mention_action", required=True)

    for act in ("add", "remove"):
        sp = sub.add_parser(act)
        sp.add_argument("id", help="Entry ID")
        sp.add_argument("name", help="Mention name (e.g. @alice)")

    ls = sub.add_parser("list")
    ls.add_argument("id", help="Entry ID")

    sr = sub.add_parser("search")
    sr.add_argument("name", help="Mention name to search for")

    sub.add_parser("all", help="List all mentions across all entries")

    p.set_defaults(func=cmd_mention)
