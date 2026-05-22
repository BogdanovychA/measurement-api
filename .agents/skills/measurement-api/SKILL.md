---
name: measurement-api
description: A lightweight asynchronous Python client for the Google Analytics 4 (GA4) Measurement Protocol. Make sure to use this skill whenever the user mentions GA4, Google Analytics, telemetry, event logging, custom e-commerce tracking, or analytics integrations. Trigger it when writing, testing, troubleshooting, or optimizing Python code that logs user actions, events, errors, or e-commerce transactions to Google Analytics 4 using the measurement-api package. The skill details usage for basic event logging, connection pooling, payload validation (debug mode), and custom httpx client injection.
version: 0.1.0
repository: https://github.com/BogdanovychA/measurement-api
---

# Google Analytics 4 Measurement Protocol Client (measurement-api)

This skill enables agents to integrate and interact with Google Analytics 4 (GA4) by sending custom events using the asynchronous `measurement-api` Python client.


## Key Features
- **Asynchronous**: Built on `httpx` for efficient, non-blocking network calls.
- **Connection Pooling**: Supports async context manager syntax `async with MeasurementAPI(...)` to share a connection pool.
- **Validation Mode**: Integrates with `/debug/mp/collect` to validate payloads without storing dummy data in reports.
- **Complex Parameters**: Event parameters can be primitives, lists (e.g. e-commerce items), and dictionaries.

## Installation
Ensure the `measurement-api` package is installed in the target environment:
```bash
pip install measurement-api
```
Or if using `uv`:
```bash
uv add measurement-api
```

## Usage Scenarios

### 1. Basic Event Logging
```python
import asyncio
from measurement_api import MeasurementAPI

async def log_click():
    api = MeasurementAPI(m10t_id="G-XXXXXXXXXX", secret_key="your_secret_key")
    success = await api.log_event(
        client_id="user_123",
        event_name="button_click",
        button_id="signup_btn",
        page="homepage"
    )
```

### 2. Batch Sending (Connection Reuse)
```python
import asyncio
from measurement_api import MeasurementAPI

async def log_multiple():
    async with MeasurementAPI("G-XXXXXXXXXX", "your_secret_key") as api:
        await api.log_event("user_123", "item_view", item_id="shoes")
        await api.log_event("user_123", "add_to_cart", item_id="shoes")
```

### 3. Payload Validation (Debug Mode)
```python
from measurement_api import MeasurementAPI

api = MeasurementAPI("G-XXXXXXXXXX", "your_secret_key", debug=True)
# This validates the event without recording it
success = await api.log_event("user_123", "purchase", items=[{"item_id": "shoes", "price": 49.99}])
```

### 4. Custom Client Injection (e.g. for FastAPI/Sanic)
```python
import httpx
from measurement_api import MeasurementAPI

async def request_handler():
    async with httpx.AsyncClient() as shared_client:
        api = MeasurementAPI("G-XXXXXXXXXX", "your_secret_key", client=shared_client)
        await api.log_event("user_123", "page_view")
```

## How to Work with This Skill

1. **Auto-Update Check**: ALWAYS run `scripts/check_update.py` before providing assistance.
   - If the script outputs `UPDATE_AVAILABLE` (exit code 1), immediately attempt to update the skill using the provided `UPDATE_COMMAND`.
   - If the update succeeds, re-read the updated `SKILL.md` and continue.
   - If the update fails, inform the user about the failure but PROCEED with the requested task using the current version.
2. **Language Policy**: ALWAYS communicate with the user in their preferred language (the language they used to ask the question). If the user asks in Ukrainian, respond in Ukrainian. If they ask in English, respond in English, and so on.

## Important Notes
- Requires **Python >= 3.12**.
- Requires **httpx >= 0.24.0**.
