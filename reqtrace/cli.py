"""Command-line interface for reqtrace replay and log inspection."""

import argparse
import json
import sys

from reqtrace.storage import LogStore
from reqtrace.replay import replay_by_id, ReplayError


def cmd_list(store: LogStore, args: argparse.Namespace) -> None:
    entries = store.all()
    if not entries:
        print("No recorded requests.")
        return
    for entry in entries:
        tag = f" [{entry.response.status_code}]" if entry.response else " [no response]"
        print(f"{entry.id}  {entry.request.method:6s}  {entry.request.url}{tag}")


def cmd_show(store: LogStore, args: argparse.Namespace) -> None:
    entry = store.get_by_id(args.id)
    if entry is None:
        print(f"Entry not found: {args.id}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(entry.to_dict(), indent=2))


def cmd_replay(store: LogStore, args: argparse.Namespace) -> None:
    try:
        response = replay_by_id(store, args.id, override_host=args.host)
    except ReplayError as exc:
        print(f"Replay failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Status: {response.status_code}")
    if args.verbose:
        for k, v in response.headers.items():
            print(f"  {k}: {v}")
    print()
    print(response.body)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reqtrace",
        description="Lightweight HTTP request logger and replay tool.",
    )
    parser.add_argument("--store", default="reqtrace_log.json", help="Path to log file")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List recorded requests")

    show_p = sub.add_parser("show", help="Show details of a request")
    show_p.add_argument("id", help="Log entry ID")

    replay_p = sub.add_parser("replay", help="Replay a recorded request")
    replay_p.add_argument("id", help="Log entry ID")
    replay_p.add_argument("--host", default=None, help="Override target host:port")
    replay_p.add_argument("-v", "--verbose", action="store_true", help="Print response headers")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    store = LogStore(path=args.store)

    dispatch = {"list": cmd_list, "show": cmd_show, "replay": cmd_replay}
    dispatch[args.command](store, args)


if __name__ == "__main__":
    main()
