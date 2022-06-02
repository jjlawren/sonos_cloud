"""Application credentials platform for sonos_cloud."""
from homeassistant.components.application_credentials import (
    AuthorizationServer,
    ClientCredential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

from .api import CustomHeadersLocalOAuth2Implementation


async def async_get_auth_implementation(
    hass: HomeAssistant, auth_domain: str, credential: ClientCredential
) -> config_entry_oauth2_flow.AbstractOAuth2Implementation:
    """Return sonos_cloud auth implementation."""
    return CustomHeadersLocalOAuth2Implementation(
        hass,
        auth_domain,
        credential,
        AuthorizationServer(
            authorize_url="https://api.sonos.com/login/v3/oauth",
            token_url="https://api.sonos.com/login/v3/oauth/access",
        ),
    )
