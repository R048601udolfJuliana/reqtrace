"""CLI sub-commands for entry ratings."""

from __future__ import annotations

import argparse

from reqtrace.rating import (
    RatingError,
    clear_rating,
    filter_by_min_rating,
    get_comment,
    get_rating,
    list_rated,
    set_rating,
)


def cmd_rating(args: argparse.Namespace, store) -> None:  # noqa: ANN001
    action = args.rating_action

    if action == "set":
        try:
            set_rating(store, args.id, args.stars, comment=args.comment or "")
            print(f"Rated entry {args.id!r}: {'★' * args.stars}")
        except RatingError as exc:
            print(f"Error: {exc}")
        except KeyError as exc:
            print(f"Not found: {exc}")

    elif action == "get":
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Entry {args.id!r} not found.")
            return
        stars = get_rating(entry)
        if stars is None:
            print(f"Entry {args.id!r} has no rating.")
        else:
            comment = get_comment(entry) or ""
            suffix = f"  # {comment}" if comment else ""
            print(f"{'★' * stars}{'☆' * (5 - stars)}{suffix}")

    elif action == "clear":
        try:
            clear_rating(store, args.id)
            print(f"Rating cleared for entry {args.id!r}.")
        except KeyError as exc:
            print(f"Not found: {exc}")

    elif action == "list":
        entries = list_rated(store)
        if not entries:
            print("No rated entries.")
            return
        for e in entries:
            stars = get_rating(e)
            comment = get_comment(e) or ""
            suffix = f"  {comment}" if comment else ""
            print(f"[{e.id}] {'★' * stars}{'☆' * (5 - stars)}  {e.request.method} {e.request.url}{suffix}")

    elif action == "filter":
        entries = filter_by_min_rating(store, args.min_stars)
        if not entries:
            print(f"No entries with rating >= {args.min_stars}.")
            return
        for e in entries:
            stars = get_rating(e)
            print(f"[{e.id}] {'★' * stars}  {e.request.method} {e.request.url}")


def add_rating_subcommand(subparsers) -> None:  # noqa: ANN001
    p = subparsers.add_parser("rating", help="Rate log entries (1-5 stars)")
    sub = p.add_subparsers(dest="rating_action", required=True)

    ps = sub.add_parser("set", help="Set a rating")
    ps.add_argument("id")
    ps.add_argument("stars", type=int, choices=range(1, 6), metavar="STARS")
    ps.add_argument("--comment", default="", help="Optional comment")

    pg = sub.add_parser("get", help="Show rating for an entry")
    pg.add_argument("id")

    pc = sub.add_parser("clear", help="Remove rating from an entry")
    pc.add_argument("id")

    sub.add_parser("list", help="List all rated entries")

    pf = sub.add_parser("filter", help="Filter entries by minimum rating")
    pf.add_argument("min_stars", type=int, choices=range(1, 6), metavar="MIN_STARS")

    p.set_defaults(func=cmd_rating)
