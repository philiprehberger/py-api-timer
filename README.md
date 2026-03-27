# philiprehberger-api-timer

[![Tests](https://github.com/philiprehberger/py-api-timer/actions/workflows/publish.yml/badge.svg)](https://github.com/philiprehberger/py-api-timer/actions/workflows/publish.yml)
[![PyPI version](https://img.shields.io/pypi/v/philiprehberger-api-timer.svg)](https://pypi.org/project/philiprehberger-api-timer/)
[![License](https://img.shields.io/github/license/philiprehberger/py-api-timer)](LICENSE)
[![Sponsor](https://img.shields.io/badge/sponsor-GitHub%20Sponsors-ec6cb9)](https://github.com/sponsors/philiprehberger)

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

### What It Does

- Adds `Server-Timing` header to every response (e.g., `Server-Timing: total;dur=42.5`)
- Logs a WARNING for requests exceeding the slow threshold
- Zero configuration required — just add the middleware

## API

| Function / Class | Description |
|------------------|-------------|
| `ASGITimerMiddleware(app, logger=None, slow_threshold_ms=500, include_header=True)` | ASGI middleware |
| `WSGITimerMiddleware(app, logger=None, slow_threshold_ms=500, include_header=True)` | WSGI middleware |


## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## License

MIT
