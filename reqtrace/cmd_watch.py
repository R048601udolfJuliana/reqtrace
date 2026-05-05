"""CLI sub-command: reqtrace watch — live-tail incoming log entries."""

import argparse
import sys

from reqtrace.storage import LogStore
from reqtrace.watchmode import watch_store


def cmd_watch(args: argparse.Namespace, store: LogStore) -> None:
    """Entry point for the 'watch' sub-command."""
    colour = not getattr(args, "no_colour", False)
    interval = getattr(args, "interval", 1.0)

    print(
        f"Watching for new requests (poll interval: {interval}s) "
        "— press Ctrl-C to stop.",
        file=sys.stderr,
    )

    try:
        watch_store(store, interval=interval, colour=colour)
    except KeyboardInterrupt:
        print("\nWatch stopped.", file=sys.stderr)


def add_watch_subcommand(subparsers) -> None:
    """Register the 'watch' sub-command on *subparsers*."""
    parser: argparse.ArgumentParser = subparsers.add_parser(
        "watch",
        help="Live-tail new log entries as they are captured by the proxy.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--no-colour",
        action="store_true",
        default=False,
        help="Disable ANSI colour output.",
    )
    parser.set_defaults(func=cmd_watch)
