"""Data models for HTTP request and response logging."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
import uuid


@dataclass
class HttpRequest:
    """Represents a captured HTTP request."""

    method: str
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None
    query_params: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "method": self.method,
            "url": self.url,
            "headers": self.headers,
            "body": self.body.decode("utf-8", errors="replace") if self.body else None,
            "query_params": self.query_params,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class HttpResponse:
    """Represents a captured HTTP response."""

    status_code: int
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[bytes] = None
    elapsed_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "status_code": self.status_code,
            "headers": self.headers,
            "body": self.body.decode("utf-8", errors="replace") if self.body else None,
            "elapsed_ms": self.elapsed_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class RequestLogEntry:
    """A paired request/response log entry."""

    request: HttpRequest
    response: Optional[HttpResponse] = None

    def to_dict(self) -> dict:
        return {
            "request": self.request.to_dict(),
            "response": self.response.to_dict() if self.response else None,
        }
