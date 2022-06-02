"""API for Sonos Cloud bound to Home Assistant OAuth."""
from base64 import b64encode
import logging
from typing import cast

from homeassistant.components.application_credentials import AuthImplementation
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)


class CustomHeadersLocalOAuth2Implementation(AuthImplementation):
    """Subclass which overrides token requests to add custom headers."""

    async def _token_request(self, data: dict) -> dict:
        """Make a token request."""
        session = async_get_clientsession(self.hass)
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
        secret = f"{self.client_id}:{self.client_secret}".encode()
        b64_encoded_secret = b64encode(secret).decode("utf-8")
        headers["Authorization"] = f"Basic {b64_encoded_secret}"
        resp = await session.post(self.token_url, data=data, headers=headers)
        if resp.status >= 400 and _LOGGER.isEnabledFor(logging.DEBUG):
            body = await resp.text()
            _LOGGER.debug(
                "Token request failed with status=%s, body=%s",
                resp.status,
                body,
            )
        resp.raise_for_status()
        return cast(dict, await resp.json())
