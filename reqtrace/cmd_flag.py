"""CLI commands for flagging/unflagging entries."""
from __future__ import annotations

import argparse
from typing import Optional

from reqtrace.flag import flag_entry, unflag_entry, list_flagged, get_flag_reason, is_flagged
from reqtrace.storage import LogStore


def cmd_flag(args: argparse.Namespace, store: LogStore) -> None:
    action: str = args.flag_action

    if action == "add":
        try:
            entry = flag_entry(store, args.id, reason=getattr(args, "reason", "") or "")
            reason = get_flag_reason(entry)
            msg = f"Flagged entry {entry.id}"
            if reason:
                msg += f" — reason: {reason}"
            print(msg)
        except KeyError as exc:
            print(str(exc))

    elif action == "remove":
        try:
            entry = unflag_entry(store, args.id)
            print(f"Unflagged entry {entry.id}")
        except KeyError as exc:
            print(str(exc))

    elif action == "list":
        entries = list_flagged(store)
        if not entries:
            print("No flagged entries.")
            return
        for e in entries:
            reason = get_flag_reason(e)
            suffix = f" [{reason}]" if reason else ""
            method = e.request.method
            url = e.request.url
            print(f"{e.id}  {method} {url}{suffix}")

    else:
        print(f"Unknown flag action: {action}")


def add_flag_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "flag", help="Flag or unflag entries for follow-up"
    )
    sub = parser.add_subparsers(dest="flag_action", required=True)

    p_add = sub.add_parser("add", help="Flag an entry")
    p_add.add_argument("id", help="Entry ID to flag")
    p_add.add_argument("--reason", default="", help="Optional reason for flagging")

    p_rm = sub.add_parser("remove", help="Unflag an entry")
    p_rm.add_argument("id", help="Entry ID to unflag")

    sub.add_parser("list", help="List all flagged entries")

    parser.set_defaults(func=cmd_flag)
