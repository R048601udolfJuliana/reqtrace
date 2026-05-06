"""CLI sub-command: transform — mutate stored entries in-place."""

from __future__ import annotations

import argparse
from typing import Optional

from reqtrace.storage import LogStore
from reqtrace.transform import build_transform_pipeline, apply_transforms


def cmd_transform(args: argparse.Namespace, store: LogStore) -> None:
    """Apply one or more transforms to entries in *store*."""
    set_headers: dict = {}
    for pair in args.set_header or []:
        if "=" not in pair:
            print(f"[transform] invalid --set-header value (expected name=value): {pair!r}")
            return
        name, _, value = pair.partition("=")
        set_headers[name.strip()] = value.strip()

    url_rewrite: Optional[tuple] = None
    if args.url_rewrite:
        parts = args.url_rewrite.split(":", 1)
        if len(parts) != 2:
            print("[transform] --url-rewrite must be in the form 'old:new'")
            return
        url_rewrite = (parts[0], parts[1])

    pipeline = build_transform_pipeline(
        set_headers=set_headers,
        remove_headers=args.remove_header or [],
        body=args.body,
        url_rewrite=url_rewrite,
    )

    if not pipeline:
        print("[transform] no transforms specified — nothing to do.")
        return

    if args.id:
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"[transform] entry {args.id!r} not found.")
            return
        targets = [entry]
    else:
        targets = store.all()

    count = 0
    for entry in targets:
        apply_transforms(entry, pipeline)
        store.update(entry)
        count += 1

    print(f"[transform] applied {len(pipeline)} transform(s) to {count} entry/entries.")


def add_transform_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("transform", help="Mutate stored request entries")
    p.add_argument("--id", metavar="ID", help="Target a single entry by ID")
    p.add_argument(
        "--set-header",
        metavar="NAME=VALUE",
        action="append",
        help="Set a request header (repeatable)",
    )
    p.add_argument(
        "--remove-header",
        metavar="NAME",
        action="append",
        help="Remove a request header (repeatable)",
    )
    p.add_argument("--body", metavar="BODY", help="Replace the request body")
    p.add_argument(
        "--url-rewrite",
        metavar="OLD:NEW",
        help="Replace OLD with NEW in the request URL",
    )
    p.set_defaults(func=cmd_transform)
