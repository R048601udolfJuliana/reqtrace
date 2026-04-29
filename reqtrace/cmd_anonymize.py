"""CLI command for anonymizing stored log entries in-place."""

from __future__ import annotations

from argparse import ArgumentParser, Namespace
from typing import Optional

from reqtrace.anonymize import anonymize_entry, DEFAULT_SENSITIVE_HEADERS
from reqtrace.storage import LogStore


def cmd_anonymize(args: Namespace, store: LogStore) -> None:
    """Anonymize one or all entries in the store."""
    extra_headers = set()
    if args.header:
        extra_headers = {h.lower() for h in args.header}
    sensitive = DEFAULT_SENSITIVE_HEADERS | extra_headers

    body_patterns = args.body_pattern or []

    if args.id:
        entry = store.get_by_id(args.id)
        if entry is None:
            print(f"Entry {args.id} not found.")
            return
        targets = [entry]
    else:
        targets = store.all()

    count = 0
    for entry in targets:
        clean = anonymize_entry(entry, sensitive_headers=sensitive, body_patterns=body_patterns)
        store.update(clean)
        count += 1

    print(f"Anonymized {count} entry/entries.")


def add_anonymize_subcommand(subparsers) -> None:
    p: ArgumentParser = subparsers.add_parser(
        "anonymize", help="Scrub sensitive data from logged requests"
    )
    p.add_argument("--id", metavar="ENTRY_ID", help="Anonymize a single entry by ID")
    p.add_argument(
        "--header",
        metavar="HEADER_NAME",
        action="append",
        help="Additional header name to redact (repeatable)",
    )
    p.add_argument(
        "--body-pattern",
        metavar="REGEX",
        action="append",
        help="Regex pattern to redact from request/response bodies (repeatable)",
    )
    p.set_defaults(func=cmd_anonymize)
