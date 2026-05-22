# -*- coding: utf-8 -*-

import logging
from types import TracebackType
from typing import Self

import httpx

logger = logging.getLogger(__name__)


class MeasurementAPI:
    """A client for interacting with the Google Analytics 4 Measurement Protocol."""

    def __init__(
        self,
        id: str,
        secret_key: str,
        *,
        debug: bool = False,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the client for sending events to Google Analytics.

        Args:
            id: Measurement ID (GA4 data stream measurement ID).
            secret_key: API Secret Key.
            debug: Debug mode (sends validation requests to the GA4 validation server).
            client: External AsyncClient for connection sharing and pooling.
        """
        self.id = id
        self.secret_key = secret_key
        self.debug = debug
        self.client = client
        self._owns_client = client is None

    async def __aenter__(self) -> Self:
        if self.client is None:
            self.client = httpx.AsyncClient()
            self._owns_client = True
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the httpx client if it was created internally within the class."""
        if self._owns_client and self.client is not None:
            await self.client.aclose()
            self.client = None

    async def log_event(self, client_id: str, event_name: str, **kwargs) -> bool:
        """Log an event in Google Analytics.

        Args:
            client_id: A unique identifier for the client.
            event_name: The name of the event.
            **kwargs: Event parameters (supports primitives, lists, and dicts).

        Returns:
            bool: True if the event was successfully sent/validated, False otherwise.
        """
        suffix = "debug/" if self.debug else ""
        base_url = f"https://www.google-analytics.com/{suffix}mp/collect"
        query_params = {"measurement_id": self.id, "api_secret": self.secret_key}

        valid_params = {
            k: v
            for k, v in kwargs.items()
            if isinstance(v, (str, int, float, bool, list, dict, tuple))
        }

        payload = {
            "client_id": client_id,
            "events": [
                {
                    "name": event_name,
                    "params": valid_params,
                }
            ],
        }

        client = self.client
        own_client = False
        if client is None:
            client = httpx.AsyncClient()
            own_client = True

        try:
            logger.debug(
                f"Sending GA event '{event_name}' to {base_url} with payload {payload}"
            )
            response = await client.post(
                base_url, params=query_params, json=payload, timeout=5.0
            )

            if self.debug:
                if response.status_code != 200:
                    logger.warning(
                        f"GA debug unexpected status: {response.status_code}"
                    )
                    return False

                debug_result = response.json()
                validation_messages = debug_result.get("validationMessages", [])

                if validation_messages:
                    logger.warning(f"GA validation issues: {validation_messages}")
                    return False
                else:
                    logger.debug(f"GA event '{event_name}' validated successfully")
                    return True
            else:
                if response.status_code == 204:
                    logger.info(f"GA event '{event_name}' sent successfully")
                    return True
                else:
                    logger.warning(
                        f"GA unexpected status {response.status_code} "
                        f"for event '{event_name}'"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error("Analytics request timeout")
            return False

        except httpx.RequestError as e:
            logger.error(f"Analytics request failed: {e}")
            return False

        except Exception as e:
            logger.exception(f"Unexpected analytics error: {e}")
            return False

        finally:
            if own_client:
                await client.aclose()
