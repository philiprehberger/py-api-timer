"""Drop-in ASGI/WSGI middleware for endpoint timing."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Iterable


__all__ = [
    "ASGITimerMiddleware",
    "WSGITimerMiddleware",
]


def _path_excluded(path: str, prefixes: tuple[str, ...]) -> bool:
    return any(path == p or path.startswith(p) for p in prefixes)


class ASGITimerMiddleware:
    """ASGI middleware that logs request duration for every endpoint.

    Args:
        app: The ASGI application.
        logger: Logger instance. Defaults to ``logging.getLogger("api_timer")``.
        slow_threshold_ms: Requests slower than this are logged at WARNING level.
        include_header: Whether to add a timing response header.
        header_name: Name of the timing header. Defaults to ``"Server-Timing"``.
        exclude_paths: Path prefixes that should bypass timing entirely
            (e.g. ``["/health", "/metrics"]``).
    """

    def __init__(
        self,
        app: Any,
        logger: logging.Logger | None = None,
        slow_threshold_ms: float = 500,
        include_header: bool = True,
        header_name: str = "Server-Timing",
        exclude_paths: Iterable[str] | None = None,
    ) -> None:
        self.app = app
        self.logger = logger or logging.getLogger("api_timer")
        self.slow_threshold_ms = slow_threshold_ms
        self.include_header = include_header
        self.header_name = header_name
        self._header_bytes = header_name.lower().encode()
        self.exclude_paths: tuple[str, ...] = tuple(exclude_paths or ())

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if self.exclude_paths and _path_excluded(path, self.exclude_paths):
            await self.app(scope, receive, send)
            return

        start = time.perf_counter_ns()
        status_code = 0

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                if self.include_header:
                    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
                    headers = list(message.get("headers", []))
                    headers.append(
                        (self._header_bytes, f"total;dur={elapsed_ms:.1f}".encode())
                    )
                    message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
            method = scope.get("method", "?")
            msg = f"{method} {path or '?'} {status_code} {elapsed_ms:.0f}ms"

            if elapsed_ms >= self.slow_threshold_ms:
                self.logger.warning(msg)
            else:
                self.logger.info(msg)


class WSGITimerMiddleware:
    """WSGI middleware that logs request duration for every endpoint.

    Args:
        app: The WSGI application.
        logger: Logger instance. Defaults to ``logging.getLogger("api_timer")``.
        slow_threshold_ms: Requests slower than this are logged at WARNING level.
        include_header: Whether to add a timing response header.
        header_name: Name of the timing header. Defaults to ``"Server-Timing"``.
        exclude_paths: Path prefixes that should bypass timing entirely.
    """

    def __init__(
        self,
        app: Callable[..., Any],
        logger: logging.Logger | None = None,
        slow_threshold_ms: float = 500,
        include_header: bool = True,
        header_name: str = "Server-Timing",
        exclude_paths: Iterable[str] | None = None,
    ) -> None:
        self.app = app
        self.logger = logger or logging.getLogger("api_timer")
        self.slow_threshold_ms = slow_threshold_ms
        self.include_header = include_header
        self.header_name = header_name
        self.exclude_paths: tuple[str, ...] = tuple(exclude_paths or ())

    def __call__(
        self, environ: dict[str, Any], start_response: Callable[..., Any]
    ) -> Any:
        path = environ.get("PATH_INFO", "")
        if self.exclude_paths and _path_excluded(path, self.exclude_paths):
            return self.app(environ, start_response)

        start = time.perf_counter_ns()
        status_holder: list[str] = []

        def timed_start_response(
            status: str, headers: list[tuple[str, str]], exc_info: Any = None
        ) -> Any:
            status_holder.append(status)
            elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
            if self.include_header:
                headers = list(headers)
                headers.append((self.header_name, f"total;dur={elapsed_ms:.1f}"))
            return start_response(status, headers, exc_info)

        try:
            return self.app(environ, timed_start_response)
        finally:
            elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
            method = environ.get("REQUEST_METHOD", "?")
            status = status_holder[0].split(" ", 1)[0] if status_holder else "?"
            msg = f"{method} {path or '?'} {status} {elapsed_ms:.0f}ms"

            if elapsed_ms >= self.slow_threshold_ms:
                self.logger.warning(msg)
            else:
                self.logger.info(msg)
