"""CLI sub-command: label — manage labels on log entries."""

from __future__ import annotations

import argparse
import sys

from reqtrace import label as label_mod
from reqtrace.storage import LogStore


def cmd_label(args: argparse.Namespace, store: LogStore) -> None:
    action = args.label_action

    if action == "add":
        try:
            label_mod.add_label(store, args.id, args.label)
            print(f"Label '{args.label}' added to {args.id}.")
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)

    elif action == "remove":
        try:
            label_mod.remove_label(store, args.id, args.label)
            print(f"Label '{args.label}' removed from {args.id}.")
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            sys.exit(1)

    elif action == "list":
        if args.id:
            try:
                labels = label_mod.get_labels(store, args.id)
            except KeyError as exc:
                print(str(exc), file=sys.stderr)
                sys.exit(1)
            if labels:
                for lbl in labels:
                    print(lbl)
            else:
                print("No labels.")
        else:
            all_labels = label_mod.list_all_labels(store)
            if all_labels:
                for lbl in all_labels:
                    print(lbl)
            else:
                print("No labels in store.")

    elif action == "filter":
        entries = label_mod.filter_by_label(store, args.label)
        if not entries:
            print(f"No entries with label '{args.label}'.")
        else:
            for e in entries:
                print(f"{e.id}  {e.request.method}  {e.request.url}")


def add_label_subcommand(subparsers) -> None:
    p = subparsers.add_parser("label", help="Manage entry labels")
    sub = p.add_subparsers(dest="label_action", required=True)

    add_p = sub.add_parser("add", help="Add a label to an entry")
    add_p.add_argument("id", help="Entry ID")
    add_p.add_argument("label", help="Label text")

    rm_p = sub.add_parser("remove", help="Remove a label from an entry")
    rm_p.add_argument("id", help="Entry ID")
    rm_p.add_argument("label", help="Label text")

    ls_p = sub.add_parser("list", help="List labels (for an entry or globally)")
    ls_p.add_argument("id", nargs="?", default=None, help="Entry ID (optional)")

    fi_p = sub.add_parser("filter", help="Show entries with a given label")
    fi_p.add_argument("label", help="Label text")

    p.set_defaults(func=cmd_label)
