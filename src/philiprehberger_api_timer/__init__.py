"""Drop-in ASGI/WSGI middleware for endpoint timing."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable


__all__ = [
    "ASGITimerMiddleware",
    "WSGITimerMiddleware",
]


class ASGITimerMiddleware:
    """ASGI middleware that logs request duration for every endpoint.

    Args:
        app: The ASGI application.
        logger: Logger instance. Defaults to ``logging.getLogger("api_timer")``.
        slow_threshold_ms: Requests slower than this are logged at WARNING level.
        include_header: Whether to add a ``Server-Timing`` response header.
    """

    def __init__(
        self,
        app: Any,
        logger: logging.Logger | None = None,
        slow_threshold_ms: float = 500,
        include_header: bool = True,
    ) -> None:
        self.app = app
        self.logger = logger or logging.getLogger("api_timer")
        self.slow_threshold_ms = slow_threshold_ms
        self.include_header = include_header

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http":
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
                        (b"server-timing", f"total;dur={elapsed_ms:.1f}".encode())
                    )
                    message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
            method = scope.get("method", "?")
            path = scope.get("path", "?")
            msg = f"{method} {path} {status_code} {elapsed_ms:.0f}ms"

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
        include_header: Whether to add a ``Server-Timing`` response header.
    """

    def __init__(
        self,
        app: Callable[..., Any],
        logger: logging.Logger | None = None,
        slow_threshold_ms: float = 500,
        include_header: bool = True,
    ) -> None:
        self.app = app
        self.logger = logger or logging.getLogger("api_timer")
        self.slow_threshold_ms = slow_threshold_ms
        self.include_header = include_header

    def __call__(
        self, environ: dict[str, Any], start_response: Callable[..., Any]
    ) -> Any:
        start = time.perf_counter_ns()
        status_holder: list[str] = []

        def timed_start_response(
            status: str, headers: list[tuple[str, str]], exc_info: Any = None
        ) -> Any:
            status_holder.append(status)
            elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
            if self.include_header:
                headers = list(headers)
                headers.append(("Server-Timing", f"total;dur={elapsed_ms:.1f}"))
            return start_response(status, headers, exc_info)

        try:
            return self.app(environ, timed_start_response)
        finally:
            elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
            method = environ.get("REQUEST_METHOD", "?")
            path = environ.get("PATH_INFO", "?")
            status = status_holder[0].split(" ", 1)[0] if status_holder else "?"
            msg = f"{method} {path} {status} {elapsed_ms:.0f}ms"

            if elapsed_ms >= self.slow_threshold_ms:
                self.logger.warning(msg)
            else:
                self.logger.info(msg)
