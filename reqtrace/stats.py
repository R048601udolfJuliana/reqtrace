"""Statistics and summary reporting for logged HTTP requests."""
from collections import Counter
from urllib.parse import urlparse
from typing import List, Dict, Any
from reqtrace.models import RequestLogEntry


def compute_stats(entries: List[RequestLogEntry]) -> Dict[str, Any]:
    """Compute summary statistics over a list of log entries."""
    if not entries:
        return {
            "total": 0,
            "methods": {},
            "status_codes": {},
            "hosts": {},
            "error_rate": 0.0,
            "avg_response_size": 0.0,
        }

    methods: Counter = Counter()
    status_codes: Counter = Counter()
    hosts: Counter = Counter()
    response_sizes: List[int] = []
    error_count = 0

    for entry in entries:
        req = entry.request
        methods[req.method.upper()] += 1

        parsed = urlparse(req.url)
        host = parsed.netloc or parsed.path
        hosts[host] += 1

        resp = entry.response
        if resp is not None:
            status_codes[resp.status_code] += 1
            if resp.body:
                response_sizes.append(len(resp.body.encode("utf-8")))
            else:
                response_sizes.append(0)
            if resp.status_code >= 400:
                error_count += 1
        else:
            status_codes["no_response"] += 1
            error_count += 1

    total = len(entries)
    avg_size = sum(response_sizes) / len(response_sizes) if response_sizes else 0.0

    return {
        "total": total,
        "methods": dict(methods),
        "status_codes": dict(status_codes),
        "hosts": dict(hosts),
        "error_rate": round(error_count / total, 4),
        "avg_response_size": round(avg_size, 2),
    }


def format_stats(stats: Dict[str, Any]) -> str:
    """Return a human-readable string representation of stats."""
    lines = [
        f"Total requests : {stats['total']}",
        f"Error rate     : {stats['error_rate'] * 100:.1f}%",
        f"Avg resp size  : {stats['avg_response_size']} bytes",
        "Methods        : " + ", ".join(f"{k}={v}" for k, v in stats["methods"].items()),
        "Status codes   : " + ", ".join(f"{k}={v}" for k, v in stats["status_codes"].items()),
        "Hosts          : " + ", ".join(f"{k}={v}" for k, v in stats["hosts"].items()),
    ]
    return "\n".join(lines)


def top_hosts(stats: Dict[str, Any], n: int = 5) -> List[tuple]:
    """Return the top N hosts by request count.

    Args:
        stats: A stats dictionary as returned by ``compute_stats``.
        n: Maximum number of hosts to return (default 5).

    Returns:
        A list of ``(host, count)`` tuples sorted by count descending.
    """
    sorted_hosts = sorted(stats["hosts"].items(), key=lambda item: item[1], reverse=True)
    return sorted_hosts[:n]
