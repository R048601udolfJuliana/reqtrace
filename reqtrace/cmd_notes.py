"""CLI subcommand for managing entry notes."""

import argparse

from reqtrace.notes import add_note, get_notes, clear_notes, list_entries_with_notes


def cmd_notes(args: argparse.Namespace, store) -> None:
    if args.notes_action == "add":
        try:
            add_note(store, args.id, args.text)
            print(f"Note added to entry {args.id}.")
        except KeyError as exc:
            print(f"Error: {exc}")
        except ValueError as exc:
            print(f"Error: {exc}")

    elif args.notes_action == "show":
        try:
            notes = get_notes(store, args.id)
        except KeyError as exc:
            print(f"Error: {exc}")
            return
        if not notes:
            print("No notes for this entry.")
        else:
            for i, note in enumerate(notes, 1):
                print(f"  [{i}] {note}")

    elif args.notes_action == "clear":
        try:
            clear_notes(store, args.id)
            print(f"Notes cleared for entry {args.id}.")
        except KeyError as exc:
            print(f"Error: {exc}")

    elif args.notes_action == "list":
        entries = list_entries_with_notes(store)
        if not entries:
            print("No entries with notes.")
        else:
            for e in entries:
                notes = e.metadata.get("__notes__", [])
                count = len(notes) if isinstance(notes, list) else 1
                print(f"  {e.id}  ({count} note(s))  {e.request.method} {e.request.url}")


def add_notes_subcommand(subparsers) -> None:
    p = subparsers.add_parser("notes", help="Manage notes on log entries")
    sub = p.add_subparsers(dest="notes_action")
    sub.required = True

    add_p = sub.add_parser("add", help="Add a note to an entry")
    add_p.add_argument("id", help="Entry ID")
    add_p.add_argument("text", help="Note text")

    show_p = sub.add_parser("show", help="Show notes for an entry")
    show_p.add_argument("id", help="Entry ID")

    clear_p = sub.add_parser("clear", help="Clear all notes from an entry")
    clear_p.add_argument("id", help="Entry ID")

    sub.add_parser("list", help="List entries that have notes")

    p.set_defaults(func=cmd_notes)
