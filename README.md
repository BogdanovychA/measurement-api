# measurement-api

A lightweight asynchronous Python client for the Google Analytics 4 (GA4) Measurement Protocol.

[![PyPI version](https://img.shields.io/pypi/v/measurement-api.svg)](https://pypi.org/project/measurement-api/)
[![Python versions](https://img.shields.io/pypi/pyversions/measurement-api.svg)](https://pypi.org/project/measurement-api/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- ⚡ **Asynchronous**: Built on top of `httpx` for efficient, non-blocking requests.
- 🔄 **Connection Pooling**: Supports async context manager syntax and custom `httpx.AsyncClient` injection to share/reuse TCP connections.
- 🐛 **Validation Mode**: Integrates with GA4's validation server `/debug/mp/collect` to verify your payloads without logging dummy events in production.
- 📦 **Complex Event Parameters**: Supports nested structures like lists (e.g. for E-commerce tracking `items`), dictionaries, and primitives.

## Installation

Install using `pip`:

```bash
pip install measurement-api
```

Or using `uv`:

```bash
uv add measurement-api
```

## Quickstart

### Basic Async Usage

```python
import asyncio
from measurement_api import MeasurementAPI

async def main():
    # Initialize the client
    api = MeasurementAPI(
        m10t_id="G-XXXXXXXXXX",
        secret_key="your_api_secret_key"
    )

    # Log an event
    success = await api.log_event(
        client_id="user_12345",
        event_name="button_click",
        button_id="submit_form",
        page_url="https://example.com"
    )

    if success:
        print("Event sent successfully!")
    else:
        print("Failed to send event.")

asyncio.run(main())
```

## Advanced Usage

### Context Manager (Connection Reuse)

When sending multiple events, use the async context manager to reuse the HTTP client's connection pool. This avoids the overhead of establishing a new TCP/TLS connection for every single event.

```python
import asyncio
from measurement_api import MeasurementAPI

async def main():
    async with MeasurementAPI("G-XXXXXXXXXX", "your_secret") as api:
        # Both events share the same connection pool
        await api.log_event("user_1", "view_item", item_name="T-Shirt")
        await api.log_event("user_1", "add_to_cart", item_name="T-Shirt")

asyncio.run(main())
```

### Passing a Custom `httpx.AsyncClient`

If your application already manages a global HTTP client (e.g. in FastAPI or Sanic), you can inject it directly:

```python
import httpx
from measurement_api import MeasurementAPI

async def send_analytics():
    # Inject your own shared client
    async with httpx.AsyncClient() as shared_client:
        api = MeasurementAPI(
            "G-XXXXXXXXXX",
            "your_secret",
            client=shared_client
        )

        # This will not close the injected client on exit or completion
        await api.log_event("user_1", "purchase", value=99.99)
```

### Debug & Validation Mode

To validate your event structure against Google's GA4 validation server, initialize the client with `debug=True`.
*Note: Events sent to the validation server do not show up in GA4 reports.*

```python
from measurement_api import MeasurementAPI

api = MeasurementAPI("G-XXXXXXXXXX", "your_secret", debug=True)

# This request goes to https://www.google-analytics.com/debug/mp/collect
# Returns True if validation passes, False if there are validation warnings/errors
success = await api.log_event("user_1", "purchase", items=[{"item_id": "SKU_123"}])
```

## Development & Testing

### Running Tests

We use `pytest` and `respx` to test the client offline without sending actual requests to Google Analytics.

1. Install dependencies:
   ```bash
   uv sync --group dev
   ```

2. Run the test suite:
   ```bash
   uv run pytest
   ```

3. Run linting checks:
   ```bash
   uv run ruff check
   ```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
