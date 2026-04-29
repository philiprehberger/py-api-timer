"""Tests for philiprehberger_api_timer."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from philiprehberger_api_timer import ASGITimerMiddleware, WSGITimerMiddleware


def test_imports() -> None:
    from philiprehberger_api_timer import ASGITimerMiddleware, WSGITimerMiddleware  # noqa: F811

    assert ASGITimerMiddleware is not None
    assert WSGITimerMiddleware is not None


class TestWSGITimerMiddleware:
    def _make_app(self, status: str = "200 OK", body: bytes = b"ok") -> Any:
        def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
            start_response(status, [("Content-Type", "text/plain")])
            return [body]

        return app

    def test_passes_through_response(self) -> None:
        app = self._make_app()
        mw = WSGITimerMiddleware(app)
        environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/test"}
        captured_status: list[str] = []
        captured_headers: list[list[tuple[str, str]]] = []

        def start_response(status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> None:
            captured_status.append(status)
            captured_headers.append(headers)

        result = mw(environ, start_response)
        assert result == [b"ok"]
        assert captured_status[0] == "200 OK"

    def test_adds_server_timing_header(self) -> None:
        app = self._make_app()
        mw = WSGITimerMiddleware(app, include_header=True)
        environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/test"}
        captured_headers: list[list[tuple[str, str]]] = []

        def start_response(status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> None:
            captured_headers.append(headers)

        mw(environ, start_response)
        header_names = [h[0] for h in captured_headers[0]]
        assert "Server-Timing" in header_names

    def test_no_server_timing_header_when_disabled(self) -> None:
        app = self._make_app()
        mw = WSGITimerMiddleware(app, include_header=False)
        environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/test"}
        captured_headers: list[list[tuple[str, str]]] = []

        def start_response(status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> None:
            captured_headers.append(headers)

        mw(environ, start_response)
        header_names = [h[0] for h in captured_headers[0]]
        assert "Server-Timing" not in header_names

    def test_logs_request(self, caplog: Any) -> None:
        app = self._make_app()
        logger = logging.getLogger("test_api_timer")
        mw = WSGITimerMiddleware(app, logger=logger)
        environ = {"REQUEST_METHOD": "POST", "PATH_INFO": "/api/items"}

        def start_response(status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> None:
            pass

        with caplog.at_level(logging.INFO, logger="test_api_timer"):
            mw(environ, start_response)

        assert any("POST /api/items" in r.message for r in caplog.records)

    def test_custom_slow_threshold(self, caplog: Any) -> None:
        app = self._make_app()
        logger = logging.getLogger("test_api_timer_slow")
        mw = WSGITimerMiddleware(app, logger=logger, slow_threshold_ms=0)
        environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/slow"}

        def start_response(status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> None:
            pass

        with caplog.at_level(logging.WARNING, logger="test_api_timer_slow"):
            mw(environ, start_response)

        assert any(r.levelno == logging.WARNING for r in caplog.records)


class TestASGITimerMiddleware:
    def test_passes_through_non_http(self) -> None:
        called = False

        async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            nonlocal called
            called = True

        mw = ASGITimerMiddleware(app)
        asyncio.run(mw({"type": "websocket"}, None, None))
        assert called

    def test_http_request_adds_header(self) -> None:
        async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        mw = ASGITimerMiddleware(app, include_header=True)
        sent_messages: list[dict[str, Any]] = []

        async def send(msg: dict[str, Any]) -> None:
            sent_messages.append(msg)

        asyncio.run(mw({"type": "http", "method": "GET", "path": "/test"}, None, send))

        start_msg = sent_messages[0]
        header_names = [h[0] for h in start_msg["headers"]]
        assert b"server-timing" in header_names

    def test_custom_header_name_asgi(self) -> None:
        async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b"ok"})

        mw = ASGITimerMiddleware(app, header_name="X-Request-Time")
        sent_messages: list[dict[str, Any]] = []

        async def send(msg: dict[str, Any]) -> None:
            sent_messages.append(msg)

        asyncio.run(mw({"type": "http", "method": "GET", "path": "/test"}, None, send))
        header_names = [h[0] for h in sent_messages[0]["headers"]]
        assert b"x-request-time" in header_names
        assert b"server-timing" not in header_names

    def test_excluded_path_skips_timing_asgi(self, caplog: Any) -> None:
        async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
            await send({"type": "http.response.start", "status": 200, "headers": []})

        logger = logging.getLogger("test_api_timer_excl_asgi")
        mw = ASGITimerMiddleware(app, logger=logger, exclude_paths=["/health"])
        sent_messages: list[dict[str, Any]] = []

        async def send(msg: dict[str, Any]) -> None:
            sent_messages.append(msg)

        with caplog.at_level(logging.INFO, logger="test_api_timer_excl_asgi"):
            asyncio.run(mw({"type": "http", "method": "GET", "path": "/health"}, None, send))

        header_names = [h[0] for h in sent_messages[0]["headers"]]
        assert b"server-timing" not in header_names
        assert not any("/health" in r.message for r in caplog.records)


class TestExclusionsWSGI:
    def test_excluded_path_skips_timing(self) -> None:
        def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
            start_response("200 OK", [("Content-Type", "text/plain")])
            return [b"ok"]

        mw = WSGITimerMiddleware(app, exclude_paths=["/metrics"])
        captured_headers: list[list[tuple[str, str]]] = []

        def start_response(status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> None:
            captured_headers.append(headers)

        mw({"REQUEST_METHOD": "GET", "PATH_INFO": "/metrics"}, start_response)
        header_names = [h[0] for h in captured_headers[0]]
        assert "Server-Timing" not in header_names

    def test_custom_header_name_wsgi(self) -> None:
        def app(environ: dict[str, Any], start_response: Any) -> list[bytes]:
            start_response("200 OK", [])
            return [b"ok"]

        mw = WSGITimerMiddleware(app, header_name="X-Request-Time")
        captured_headers: list[list[tuple[str, str]]] = []

        def start_response(status: str, headers: list[tuple[str, str]], exc_info: Any = None) -> None:
            captured_headers.append(headers)

        mw({"REQUEST_METHOD": "GET", "PATH_INFO": "/test"}, start_response)
        header_names = [h[0] for h in captured_headers[0]]
        assert "X-Request-Time" in header_names
        assert "Server-Timing" not in header_names
