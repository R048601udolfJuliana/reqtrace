"""CLI subcommand for milestone management."""

from __future__ import annotations

import argparse

from reqtrace import milestone as ms


def cmd_milestone(args: argparse.Namespace, store) -> None:
    action = args.milestone_action

    if action == "set":
        try:
            ms.set_milestone(store, args.id, args.name)
            print(f"Milestone '{args.name}' set on entry {args.id}.")
        except ms.MilestoneError as exc:
            print(f"Error: {exc}")

    elif action == "reach":
        try:
            ms.mark_reached(store, args.id)
            name = ms.get_milestone(store, args.id)
            print(f"Milestone '{name}' marked as reached for entry {args.id}.")
        except ms.MilestoneError as exc:
            print(f"Error: {exc}")

    elif action == "clear":
        try:
            ms.clear_milestone(store, args.id)
            print(f"Milestone cleared from entry {args.id}.")
        except ms.MilestoneError as exc:
            print(f"Error: {exc}")

    elif action == "show":
        name = ms.get_milestone(store, args.id)
        if name is None:
            print(f"No milestone set on entry {args.id}.")
        else:
            reached = ms.is_reached(store, args.id)
            status = "reached" if reached else "pending"
            print(f"Milestone: {name}  [{status}]")

    elif action == "list":
        items = ms.list_milestones(store)
        if not items:
            print("No milestones found.")
        else:
            for item in items:
                status = "✓" if item["reached"] else "○"
            print(f"  [{status}] {item['id']}  {item['milestone']}")


def add_milestone_subcommand(subparsers) -> None:
    p = subparsers.add_parser("milestone", help="Manage milestones on entries.")
    sub = p.add_subparsers(dest="milestone_action", required=True)

    s = sub.add_parser("set", help="Set a milestone on an entry.")
    s.add_argument("id", help="Entry ID.")
    s.add_argument("name", help="Milestone name.")

    r = sub.add_parser("reach", help="Mark a milestone as reached.")
    r.add_argument("id", help="Entry ID.")

    c = sub.add_parser("clear", help="Clear the milestone from an entry.")
    c.add_argument("id", help="Entry ID.")

    sh = sub.add_parser("show", help="Show the milestone for an entry.")
    sh.add_argument("id", help="Entry ID.")

    sub.add_parser("list", help="List all entries with milestones.")

    p.set_defaults(func=cmd_milestone)
