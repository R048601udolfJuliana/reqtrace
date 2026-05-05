"""CLI sub-commands for snapshot save/load."""

from __future__ import annotations

import sys
from pathlib import Path

from reqtrace.snapshot import (
    SnapshotError,
    load_snapshot,
    save_snapshot,
    snapshot_from_json,
    snapshot_to_json,
)


def cmd_snapshot(args, store) -> None:
    """Dispatch snapshot sub-commands."""
    if args.snapshot_cmd == "save":
        _cmd_save(args, store)
    elif args.snapshot_cmd == "load":
        _cmd_load(args, store)
    else:
        print("Unknown snapshot command. Use 'save' or 'load'.", file=sys.stderr)
        sys.exit(1)


def _cmd_save(args, store) -> None:
    name = args.name or "default"
    snapshot = save_snapshot(store, name)
    text = snapshot_to_json(snapshot)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
        print(f"Snapshot '{name}' saved to {args.output} ({len(snapshot['entries'])} entries).")
    else:
        print(text)


def _cmd_load(args, store) -> None:
    if not args.input:
        print("--input FILE is required for snapshot load.", file=sys.stderr)
        sys.exit(1)
    try:
        text = Path(args.input).read_text(encoding="utf-8")
        snapshot = snapshot_from_json(text)
        count = load_snapshot(store, snapshot)
        print(f"Loaded {count} entries from snapshot '{snapshot.get('name', 'unknown')}'.")
    except (SnapshotError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def add_snapshot_subcommand(subparsers) -> None:
    snap_parser = subparsers.add_parser("snapshot", help="Save or load a store snapshot")
    snap_sub = snap_parser.add_subparsers(dest="snapshot_cmd")

    save_p = snap_sub.add_parser("save", help="Save current store to a snapshot file")
    save_p.add_argument("--name", default="default", help="Snapshot name")
    save_p.add_argument("--output", "-o", metavar="FILE", help="Output file (default: stdout)")

    load_p = snap_sub.add_parser("load", help="Load entries from a snapshot file")
    load_p.add_argument("--input", "-i", metavar="FILE", required=True, help="Snapshot file to load")
