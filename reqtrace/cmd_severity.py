"""CLI sub-command for managing entry severity levels."""

from __future__ import annotations

import argparse

from reqtrace.severity import (
    SEVERITY_LEVELS,
    SeverityError,
    clear_severity,
    filter_by_severity,
    get_severity,
    set_severity,
)


def cmd_severity(args: argparse.Namespace, store) -> None:  # type: ignore[type-arg]
    action = args.severity_action

    if action == "set":
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Entry '{args.id}' not found.")
            return
        try:
            set_severity(entry, args.level)
        except SeverityError as exc:
            print(str(exc))
            return
        store.save()
        print(f"Severity set to '{args.level}' on entry {args.id}.")

    elif action == "get":
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Entry '{args.id}' not found.")
            return
        level = get_severity(entry)
        print(level if level else "(no severity set)")

    elif action == "clear":
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Entry '{args.id}' not found.")
            return
        clear_severity(entry)
        store.save()
        print(f"Severity cleared on entry {args.id}.")

    elif action == "list":
        level = getattr(args, "level", None)
        if level:
            entries = filter_by_severity(store, level)
            if not entries:
                print(f"No entries with severity '{level}'.")
            for e in entries:
                print(f"  {e.id}  {e.request.method}  {e.request.url}")
        else:
            for e in store.all():
                lvl = get_severity(e)
                if lvl:
                    print(f"  {e.id}  [{lvl}]  {e.request.method}  {e.request.url}")


def add_severity_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("severity", help="Manage severity levels on entries")
    sub = p.add_subparsers(dest="severity_action", required=True)

    s = sub.add_parser("set", help="Set severity level")
    s.add_argument("id", help="Entry ID")
    s.add_argument("level", choices=SEVERITY_LEVELS, help="Severity level")

    g = sub.add_parser("get", help="Get severity level")
    g.add_argument("id", help="Entry ID")

    c = sub.add_parser("clear", help="Clear severity level")
    c.add_argument("id", help="Entry ID")

    ls = sub.add_parser("list", help="List entries by severity")
    ls.add_argument("level", choices=SEVERITY_LEVELS, nargs="?", help="Filter by level")

    p.set_defaults(func=cmd_severity)
