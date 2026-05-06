"""CLI command for comparing two stored log entries."""

from __future__ import annotations

import argparse

from reqtrace.compare import compare_entries
from reqtrace.storage import LogStore


def _print_comparison_table(entry_a, entry_b, result) -> None:
    """Print a formatted comparison table for two log entries."""
    ra, rb = entry_a.request, entry_b.request

    print(f"{'Field':<12}  {'Entry A':<35}  {'Entry B':<35}  {'Score':>6}")
    print("-" * 95)
    print(f"{'method':<12}  {ra.method:<35}  {rb.method:<35}  {result.field_scores['method']:>6.0%}")
    print(f"{'url':<12}  {ra.url[:35]:<35}  {rb.url[:35]:<35}  {result.field_scores['url']:>6.0%}")
    print(f"{'headers':<12}  {'(dict)':<35}  {'(dict)':<35}  {result.field_scores['headers']:>6.0%}")
    body_a = (ra.body or "")[:35]
    body_b = (rb.body or "")[:35]
    print(f"{'body':<12}  {body_a:<35}  {body_b:<35}  {result.field_scores['body']:>6.0%}")
    print("-" * 95)
    print(result.summary)


def cmd_compare(args: argparse.Namespace, store: LogStore) -> None:
    """Compare two stored log entries by ID and print a similarity report."""
    entry_a = store.get_by_id(args.id_a)
    if entry_a is None:
        print(f"Entry not found: {args.id_a}")
        return

    entry_b = store.get_by_id(args.id_b)
    if entry_b is None:
        print(f"Entry not found: {args.id_b}")
        return

    result = compare_entries(entry_a, entry_b)
    _print_comparison_table(entry_a, entry_b, result)


def add_compare_subcommand(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("compare", help="Compare two log entries by similarity")
    p.add_argument("id_a", help="ID of the first entry")
    p.add_argument("id_b", help="ID of the second entry")
    p.set_defaults(func=cmd_compare)
