"""Watch mode: monitor the log store and print new entries as they arrive."""

import time
from typing import Callable, Optional

from reqtrace.storage import LogStore
from reqtrace.highlight import method_colour, status_colour, url_highlight


def _format_entry(entry, colour: bool = True) -> str:
    """Return a single-line summary of a log entry for watch output."""
    req = entry.request
    resp = entry.response

    method = method_colour(req.method, enabled=colour)
    url = url_highlight(req.url, enabled=colour)

    if resp is not None:
        status = status_colour(resp.status_code, enabled=colour)
        size = len(resp.body or "") if resp.body else 0
        return f"[{entry.id[:8]}]  {method}  {url}  →  {status}  ({size}b)"
    else:
        return f"[{entry.id[:8]}]  {method}  {url}  →  (no response)"


def watch_store(
    store: LogStore,
    interval: float = 1.0,
    colour: bool = True,
    max_iterations: Optional[int] = None,
    on_entry: Optional[Callable] = None,
) -> None:
    """
    Poll *store* every *interval* seconds and print any new entries.

    Parameters
    ----------
    store:          The LogStore to watch.
    interval:       Polling interval in seconds.
    colour:         Whether to emit ANSI colour codes.
    max_iterations: Stop after this many poll cycles (useful for tests).
    on_entry:       Optional callback invoked with each new entry.
    """
    seen_ids: set = set()
    iterations = 0

    while True:
        current = {e.id: e for e in store.all()}
        new_ids = set(current.keys()) - seen_ids

        for eid in sorted(new_ids, key=lambda i: current[i].timestamp):
            entry = current[eid]
            line = _format_entry(entry, colour=colour)
            print(line)
            if on_entry is not None:
                on_entry(entry)

        seen_ids.update(new_ids)
        iterations += 1

        if max_iterations is not None and iterations >= max_iterations:
            break

        time.sleep(interval)
