"""CLI command for displaying request log statistics."""
from reqtrace.storage import LogStore
from reqtrace.filter import FilterCriteria, apply_filter
from reqtrace.stats import compute_stats, format_stats


def cmd_stats(args, store: LogStore) -> None:
    """Print statistics for logged requests, optionally filtered."""
    entries = store.all()

    criteria = FilterCriteria(
        method=getattr(args, "method", None),
        host=getattr(args, "host", None),
        status_code=getattr(args, "status", None),
    )
    entries = apply_filter(entries, criteria)

    if not entries:
        print("No entries found.")
        return

    stats = compute_stats(entries)
    print(format_stats(stats))


def add_stats_subcommand(subparsers) -> None:
    """Register the 'stats' subcommand on the given subparsers object."""
    p = subparsers.add_parser("stats", help="Show statistics for captured requests")
    p.add_argument("--method", default=None, help="Filter by HTTP method")
    p.add_argument("--host", default=None, help="Filter by host substring")
    p.add_argument("--status", type=int, default=None, help="Filter by HTTP status code")
    p.set_defaults(func=cmd_stats)
