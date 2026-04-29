"""CLI subcommand for exporting logged requests to JSON or cURL format."""

from __future__ import annotations

import sys
from argparse import ArgumentParser, Namespace

from reqtrace.exporter import export_curl, export_json
from reqtrace.storage import LogStore


def cmd_export(args: Namespace, store: LogStore) -> int:
    """Export entries from the store to the requested format.

    Returns an exit code (0 = success, 1 = error).
    """
    entries = store.all()

    if args.id:
        entries = [e for e in entries if e.id == args.id]
        if not entries:
            print(f"No entry found with id '{args.id}'", file=sys.stderr)
            return 1

    if not entries:
        print("No entries to export.", file=sys.stderr)
        return 0

    fmt = args.format.lower()

    if fmt == "json":
        output = export_json(entries)
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as fh:
                    fh.write(output)
                print(f"Exported {len(entries)} entry/entries to {args.output}")
            except OSError as exc:
                print(f"Failed to write file: {exc}", file=sys.stderr)
                return 1
        else:
            print(output)

    elif fmt == "curl":
        lines = export_curl(entries)
        if args.output:
            try:
                with open(args.output, "w", encoding="utf-8") as fh:
                    fh.write("\n".join(lines) + "\n")
                print(f"Exported {len(entries)} entry/entries to {args.output}")
            except OSError as exc:
                print(f"Failed to write file: {exc}", file=sys.stderr)
                return 1
        else:
            for line in lines:
                print(line)
    else:
        print(f"Unknown format '{fmt}'. Use 'json' or 'curl'.", file=sys.stderr)
        return 1

    return 0


def add_export_subcommand(subparsers) -> None:  # type: ignore[type-arg]
    """Register the 'export' subcommand on *subparsers*."""
    parser: ArgumentParser = subparsers.add_parser(
        "export",
        help="Export logged requests to JSON or cURL format",
    )
    parser.add_argument(
        "--format",
        choices=["json", "curl"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--id",
        default=None,
        metavar="ENTRY_ID",
        help="Export a single entry by ID",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        metavar="FILE",
        help="Write output to FILE instead of stdout",
    )
    parser.set_defaults(func=cmd_export)
