import time
from philiprehberger_api_timer import ASGITimerMiddleware, WSGITimerMiddleware


def test_wsgi_middleware_adds_header():
    def app(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"hello"]

    middleware = WSGITimerMiddleware(app, slow_threshold_ms=10000)

    captured_headers = {}

    def mock_start_response(status, headers, exc_info=None):
        captured_headers.update(dict(headers))

    environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/test"}
    result = middleware(environ, mock_start_response)
    assert result == [b"hello"]
    assert "Server-Timing" in captured_headers
    assert "total;dur=" in captured_headers["Server-Timing"]


def test_wsgi_timing_value_is_positive():
    def app(environ, start_response):
        time.sleep(0.01)
        start_response("200 OK", [])
        return [b"ok"]

    middleware = WSGITimerMiddleware(app)
    captured = {}

    def mock_start(status, headers, exc_info=None):
        captured.update(dict(headers))

    middleware({"REQUEST_METHOD": "GET", "PATH_INFO": "/"}, mock_start)
    timing = captured["Server-Timing"]
    dur = float(timing.split("dur=")[1])
    assert dur > 0


class TestASGIMiddleware:
    def test_instantiation(self):
        async def app(scope, receive, send):
            pass
        middleware = ASGITimerMiddleware(app)
        assert middleware is not None

    def test_custom_threshold(self):
        async def app(scope, receive, send):
            pass
        middleware = ASGITimerMiddleware(app, slow_threshold_ms=200)
        assert middleware.slow_threshold_ms == 200
