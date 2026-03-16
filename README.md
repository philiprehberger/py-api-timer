# philiprehberger-api-timer

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

### What It Does

- Adds `Server-Timing` header to every response (e.g., `Server-Timing: total;dur=42.5`)
- Logs a WARNING for requests exceeding the slow threshold
- Zero configuration required — just add the middleware

## API

- `ASGITimerMiddleware(app, slow_threshold_ms=500)` — ASGI middleware
- `WSGITimerMiddleware(app, slow_threshold_ms=500)` — WSGI middleware


## Development

```bash
pip install -e .
python -m pytest tests/ -v
```

## License

MIT
