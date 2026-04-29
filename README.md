# philiprehberger-api-timer

[![Tests](https://github.com/philiprehberger/py-api-timer/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-api-timer/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-api-timer.svg)](https://pypi.org/project/philiprehberger-api-timer/)
[![Last updated](https://img.shields.io/github/last-commit/philiprehberger/py-api-timer)](https://github.com/philiprehberger/py-api-timer/commits/main)

Drop-in ASGI/WSGI middleware for endpoint timing with Server-Timing headers.

## Installation

```bash
pip install philiprehberger-api-timer
```

## Usage

### ASGI (FastAPI, Starlette)

```python
from fastapi import FastAPI
from philiprehberger_api_timer import ASGITimerMiddleware

app = FastAPI()
app.add_middleware(ASGITimerMiddleware, slow_threshold_ms=500)
```

### WSGI (Flask, Django)

```python
from flask import Flask
from philiprehberger_api_timer import WSGITimerMiddleware

app = Flask(__name__)
app.wsgi_app = WSGITimerMiddleware(app.wsgi_app, slow_threshold_ms=500)
```

### Custom Logger

```python
import logging
from philiprehberger_api_timer import ASGITimerMiddleware

logger = logging.getLogger("my_api")
app.add_middleware(ASGITimerMiddleware, logger=logger, include_header=False)
```

### Exclude Paths

```python
from philiprehberger_api_timer import ASGITimerMiddleware

app.add_middleware(
    ASGITimerMiddleware,
    exclude_paths=["/health", "/metrics"],  # bypass timing entirely
)
```

### Custom Header Name

```python
from philiprehberger_api_timer import WSGITimerMiddleware

app.wsgi_app = WSGITimerMiddleware(app.wsgi_app, header_name="X-Request-Time")
```

### What It Does

- Adds `Server-Timing` header to every response (e.g., `Server-Timing: total;dur=42.5`)
- Logs a WARNING for requests exceeding the slow threshold
- Zero configuration required — just add the middleware

## API

| Function / Class | Description |
|------------------|-------------|
| `ASGITimerMiddleware(app, logger=None, slow_threshold_ms=500, include_header=True, header_name="Server-Timing", exclude_paths=None)` | ASGI middleware |
| `WSGITimerMiddleware(app, logger=None, slow_threshold_ms=500, include_header=True, header_name="Server-Timing", exclude_paths=None)` | WSGI middleware |

## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## Support

If you find this project useful:

⭐ [Star the repo](https://github.com/philiprehberger/py-api-timer)

🐛 [Report issues](https://github.com/philiprehberger/py-api-timer/issues?q=is%3Aissue+is%3Aopen+label%3Abug)

💡 [Suggest features](https://github.com/philiprehberger/py-api-timer/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)

❤️ [Sponsor development](https://github.com/sponsors/philiprehberger)

🌐 [All Open Source Projects](https://philiprehberger.com/open-source-packages)

💻 [GitHub Profile](https://github.com/philiprehberger)

🔗 [LinkedIn Profile](https://www.linkedin.com/in/philiprehberger)

## License

[MIT](LICENSE)
