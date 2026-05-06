"""Rate-limit analysis for logged HTTP entries."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from reqtrace.models import RequestLogEntry
from reqtrace.timeline import _parse_ts


@dataclass
class HostRateInfo:
    host: str
    total_requests: int
    window_seconds: float
    requests_per_second: float
    peak_requests_in_window: int
    flagged: bool  # True when rps exceeds threshold

    def summary(self) -> str:
        flag = " [FLAGGED]" if self.flagged else ""
        return (
            f"{self.host}: {self.total_requests} reqs over "
            f"{self.window_seconds:.1f}s "
            f"({self.requests_per_second:.2f} req/s){flag}"
        )


def _extract_host(entry: RequestLogEntry) -> str:
    url = entry.request.url
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc or url
    except Exception:
        return url


def analyze_rate_limits(
    entries: List[RequestLogEntry],
    threshold_rps: float = 10.0,
    window_seconds: float = 60.0,
) -> Dict[str, HostRateInfo]:
    """Group entries by host and compute request rates.

    Args:
        entries: Log entries to analyse.
        threshold_rps: Requests-per-second above which a host is flagged.
        window_seconds: Rolling window size used for peak detection.

    Returns:
        Mapping of host -> HostRateInfo.
    """
    by_host: Dict[str, List[float]] = defaultdict(list)

    for entry in entries:
        ts = _parse_ts(entry.timestamp)
        if ts is None:
            continue
        host = _extract_host(entry)
        by_host[host].append(ts.timestamp())

    results: Dict[str, HostRateInfo] = {}
    for host, timestamps in by_host.items():
        timestamps.sort()
        total = len(timestamps)
        span = (timestamps[-1] - timestamps[0]) if len(timestamps) > 1 else 0.0
        rps = total / span if span > 0 else float(total)

        # Peak: max requests in any rolling window_seconds slice
        peak = 0
        for i, t in enumerate(timestamps):
            count = sum(1 for t2 in timestamps[i:] if t2 - t <= window_seconds)
            if count > peak:
                peak = count

        results[host] = HostRateInfo(
            host=host,
            total_requests=total,
            window_seconds=span,
            requests_per_second=rps,
            peak_requests_in_window=peak,
            flagged=rps > threshold_rps,
        )

    return results


def format_rate_report(info_map: Dict[str, HostRateInfo]) -> str:
    """Return a human-readable rate-limit report."""
    if not info_map:
        return "No entries to analyse."
    lines = ["Rate-limit analysis:", "-" * 40]
    for info in sorted(info_map.values(), key=lambda i: -i.requests_per_second):
        lines.append(info.summary())
    return "\n".join(lines)
