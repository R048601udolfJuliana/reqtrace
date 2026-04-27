"""HTTP proxy middleware for intercepting and logging requests/responses."""

import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, urlencode
import json

from reqtrace.models import HttpRequest, HttpResponse, RequestLogEntry
from reqtrace.storage import LogStore


class ProxyHandler(BaseHTTPRequestHandler):
    """HTTP request handler that forwards requests to a target and logs them."""

    # Target base URL set by the proxy server
    target_base_url: str = ""
    log_store: LogStore = None

    def _forward_request(self, body: bytes | None = None):
        """Forward the incoming request to the target server and log the exchange."""
        target_url = self.target_base_url + self.path

        # Collect incoming headers (exclude hop-by-hop headers)
        headers = {}
        hop_by_hop = {"connection", "keep-alive", "proxy-authenticate",
                      "proxy-authorization", "te", "trailers",
                      "transfer-encoding", "upgrade"}
        for key, value in self.headers.items():
            if key.lower() not in hop_by_hop:
                headers[key] = value

        # Build the logged request object
        logged_request = HttpRequest(
            method=self.command,
            url=target_url,
            headers=dict(headers),
            body=body.decode("utf-8", errors="replace") if body else None,
        )

        # Forward the request
        req = Request(target_url, data=body, headers=headers, method=self.command)
        start_time = time.time()
        logged_response = None

        try:
            with urlopen(req, timeout=15) as resp:
                elapsed_ms = int((time.time() - start_time) * 1000)
                response_body = resp.read()
                response_headers = dict(resp.headers)
                logged_response = HttpResponse(
                    status_code=resp.status,
                    headers=response_headers,
                    body=response_body.decode("utf-8", errors="replace"),
                    elapsed_ms=elapsed_ms,
                )

                # Send response back to the original client
                self.send_response(resp.status)
                for k, v in response_headers.items():
                    if k.lower() not in hop_by_hop:
                        self.send_header(k, v)
                self.end_headers()
                self.wfile.write(response_body)

        except HTTPError as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            response_body = e.read()
            logged_response = HttpResponse(
                status_code=e.code,
                headers=dict(e.headers),
                body=response_body.decode("utf-8", errors="replace"),
                elapsed_ms=elapsed_ms,
            )
            self.send_response(e.code)
            self.end_headers()
            self.wfile.write(response_body)

        except URLError as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Proxy error: {e.reason}".encode())

        finally:
            # Always log the entry, even if the upstream request failed
            entry = RequestLogEntry(
                id=str(uuid.uuid4()),
                request=logged_request,
                response=logged_response,
            )
            self.log_store.add(entry)
            status = logged_response.status_code if logged_response else "ERR"
            print(f"[reqtrace] {self.command} {self.path} -> {status}")

    def do_GET(self):
        self._forward_request()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else None
        self._forward_request(body)

    def do_PUT(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else None
        self._forward_request(body)

    def do_PATCH(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else None
        self._forward_request(body)

    def do_DELETE(self):
        self._forward_request()

    def log_message(self, format, *args):
        """Suppress default access log output; we handle logging ourselves."""
        pass


def run_proxy(target_url: str, host: str = "127.0.0.1", port: int = 8888,
              store: LogStore = None) -> None:
    """Start the proxy server.

    Args:
        target_url: Base URL of the upstream API (e.g. 'http://localhost:3000').
        host: Interface to bind to.
        port: Port to listen on.
        store: Optional LogStore instance; a new one is created if not provided.
    """
    if store is None:
        store = LogStore()

    # Inject shared state into the handler class
    ProxyHandler.target_base_url = target_url.rstrip("/")
    ProxyHandler.log_store = store

    server = HTTPServer((host, port), ProxyHandler)
    print(f"[reqtrace] Proxying {host}:{port} -> {target_url}")
    print("[reqtrace] Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[reqtrace] Shutting down.")
    finally:
        server.server_close()
