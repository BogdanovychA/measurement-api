# -*- coding: utf-8 -*-

import httpx
import pytest
import respx

from measurement_api import MeasurementAPI

pytestmark = pytest.mark.asyncio


@respx.mock
async def test_log_event_success() -> None:
    api = MeasurementAPI("G-12345", "secret_abc")

    route = respx.post("https://www.google-analytics.com/mp/collect").mock(
        return_value=httpx.Response(204)
    )

    result = await api.log_event("client_1", "test_event", param1="value1", num=42)

    assert result is True
    assert route.called
    request = route.calls.last.request
    assert "measurement_id=G-12345" in request.url.query.decode()
    assert "api_secret=secret_abc" in request.url.query.decode()

    # Verify JSON payload
    import json

    payload = json.loads(request.content)
    assert payload["client_id"] == "client_1"
    assert payload["events"][0]["name"] == "test_event"
    assert payload["events"][0]["params"] == {"param1": "value1", "num": 42}


@respx.mock
async def test_log_event_debug_validation_success() -> None:
    api = MeasurementAPI("G-12345", "secret_abc", debug=True)

    route = respx.post("https://www.google-analytics.com/debug/mp/collect").mock(
        return_value=httpx.Response(200, json={"validationMessages": []})
    )

    result = await api.log_event("client_1", "test_event")

    assert result is True
    assert route.called


@respx.mock
async def test_log_event_debug_validation_failure() -> None:
    api = MeasurementAPI("G-12345", "secret_abc", debug=True)

    route = respx.post("https://www.google-analytics.com/debug/mp/collect").mock(
        return_value=httpx.Response(
            200,
            json={
                "validationMessages": [
                    {
                        "description": "Measurement ID is invalid",
                        "validationCode": "VALUE_INVALID",
                    }
                ]
            },
        )
    )

    result = await api.log_event("client_1", "test_event")

    assert result is False
    assert route.called


@respx.mock
async def test_log_event_unexpected_status() -> None:
    api = MeasurementAPI("G-12345", "secret_abc")

    respx.post("https://www.google-analytics.com/mp/collect").mock(
        return_value=httpx.Response(500)
    )

    result = await api.log_event("client_1", "test_event")
    assert result is False


@respx.mock
async def test_log_event_debug_unexpected_status() -> None:
    api = MeasurementAPI("G-12345", "secret_abc", debug=True)

    respx.post("https://www.google-analytics.com/debug/mp/collect").mock(
        return_value=httpx.Response(400)
    )

    result = await api.log_event("client_1", "test_event")
    assert result is False


@respx.mock
async def test_log_event_parameter_filtering() -> None:
    api = MeasurementAPI("G-12345", "secret_abc")

    route = respx.post("https://www.google-analytics.com/mp/collect").mock(
        return_value=httpx.Response(204)
    )

    # We send valid parameters (primitives, list, dict, tuple) and an invalid parameter (set)
    result = await api.log_event(
        "client_1",
        "purchase",
        str_val="ok",
        int_val=10,
        float_val=10.5,
        bool_val=True,
        list_val=[{"item_id": "1"}],
        dict_val={"nested": "yes"},
        tuple_val=(1, 2),
        invalid_val={1, 2, 3},  # Set is not valid and should be filtered out
    )

    assert result is True
    import json

    payload = json.loads(route.calls.last.request.content)
    params = payload["events"][0]["params"]

    assert params["str_val"] == "ok"
    assert params["int_val"] == 10
    assert params["float_val"] == 10.5
    assert params["bool_val"] is True
    assert params["list_val"] == [{"item_id": "1"}]
    assert params["dict_val"] == {"nested": "yes"}
    assert params["tuple_val"] == [1, 2]  # JSON converts tuple to list
    assert "invalid_val" not in params


@respx.mock
async def test_shared_client_reuse() -> None:
    async with httpx.AsyncClient() as shared_client:
        api = MeasurementAPI("G-12345", "secret_abc", client=shared_client)

        route = respx.post("https://www.google-analytics.com/mp/collect").mock(
            return_value=httpx.Response(204)
        )

        result1 = await api.log_event("client_1", "event_1")
        result2 = await api.log_event("client_1", "event_2")

        assert result1 is True
        assert result2 is True
        assert route.call_count == 2

        # Verify client is not closed by the API
        assert not shared_client.is_closed

    # The block exit closes the client
    assert shared_client.is_closed


@respx.mock
async def test_context_manager_lifecycle() -> None:
    api_instance = None
    async with MeasurementAPI("G-12345", "secret_abc") as api:
        api_instance = api
        assert api.client is not None
        assert not api.client.is_closed

        respx.post("https://www.google-analytics.com/mp/collect").mock(
            return_value=httpx.Response(204)
        )
        result = await api.log_event("client_1", "event_1")
        assert result is True

    # After exiting the context manager, client should be closed and set to None
    assert api_instance.client is None


@respx.mock
async def test_exceptions_handling() -> None:
    api = MeasurementAPI("G-12345", "secret_abc")

    # 1. TimeoutException
    respx.post("https://www.google-analytics.com/mp/collect").mock(
        side_effect=httpx.TimeoutException("Timeout")
    )
    result = await api.log_event("client_1", "event_1")
    assert result is False

    # 2. RequestError
    respx.post("https://www.google-analytics.com/mp/collect").mock(
        side_effect=httpx.RequestError("Request failed")
    )
    result = await api.log_event("client_1", "event_1")
    assert result is False

    # 3. Generic unexpected exception
    respx.post("https://www.google-analytics.com/mp/collect").mock(
        side_effect=ValueError("Unexpected error")
    )
    result = await api.log_event("client_1", "event_1")
    assert result is False
