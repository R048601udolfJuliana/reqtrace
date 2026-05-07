"""CLI sub-command for managing entry reminders."""

from __future__ import annotations

import argparse
from typing import Any

from reqtrace.remind import (
    ReminderError,
    clear_reminder,
    get_reminder,
    is_due,
    list_due,
    set_reminder,
)
from reqtrace.storage import LogStore


def cmd_remind(args: argparse.Namespace, store: LogStore) -> None:
    action = args.remind_action

    if action == "set":
        try:
            entry = set_reminder(store, args.id, args.minutes, args.note or "")
        except ReminderError as exc:
            print(f"Error: {exc}")
            return
        remind_at = get_reminder(entry)
        print(f"Reminder set for entry {args.id} at {remind_at.isoformat()}")
        if args.note:
            print(f"Note: {args.note}")

    elif action == "clear":
        try:
            clear_reminder(store, args.id)
        except ReminderError as exc:
            print(f"Error: {exc}")
            return
        print(f"Reminder cleared for entry {args.id}")

    elif action == "show":
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Error: Entry not found: {args.id}")
            return
        remind_at = get_reminder(entry)
        if remind_at is None:
            print(f"No reminder set for entry {args.id}")
        else:
            due_label = " [DUE]" if is_due(entry) else ""
            note = entry.metadata.get("remind_note", "")
            print(f"Reminder: {remind_at.isoformat()}{due_label}")
            if note:
                print(f"Note: {note}")

    elif action == "due":
        entries = list_due(store)
        if not entries:
            print("No reminders are currently due.")
            return
        for e in entries:
            remind_at = get_reminder(e)
            note = e.metadata.get("remind_note", "")
            line = f"{e.id}  {e.request.method} {e.request.url}  due={remind_at.isoformat()}"
            if note:
                line += f"  note={note!r}"
            print(line)


def add_remind_subcommand(subparsers: Any) -> None:
    p = subparsers.add_parser("remind", help="Manage reminders for log entries")
    sp = p.add_subparsers(dest="remind_action", required=True)

    s = sp.add_parser("set", help="Set a reminder")
    s.add_argument("id", help="Entry ID")
    s.add_argument("minutes", type=int, help="Minutes from now")
    s.add_argument("--note", default="", help="Optional reminder note")

    c = sp.add_parser("clear", help="Clear a reminder")
    c.add_argument("id", help="Entry ID")

    sh = sp.add_parser("show", help="Show reminder for an entry")
    sh.add_argument("id", help="Entry ID")

    sp.add_parser("due", help="List all due reminders")

    p.set_defaults(func=cmd_remind)
