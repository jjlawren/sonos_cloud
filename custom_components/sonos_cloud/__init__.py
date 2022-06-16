"""The Sonos Cloud integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.application_credentials import (
    ClientCredential,
    async_import_client_credential,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_entry_oauth2_flow, config_validation as cv

from .const import DOMAIN, PLAYERS, SESSION

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["media_player"]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Sonos Cloud component."""
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][PLAYERS] = []

    if DOMAIN not in config:
        return True

    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
        ),
    )

    _LOGGER.warning(
        "Application Credentials have been imported and can be removed from configuration.yaml"
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sonos Cloud from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(
            hass, entry
        )
    )

    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    hass.data[DOMAIN][SESSION] = session

    url = "https://api.ws.sonos.com/control/api/v1/households"
    result = await session.async_request("get", url)
    if result.status >= 400:
        body = await result.text()
        _LOGGER.error(
            "Household request failed (%s): %s",
            result.status,
            body,
        )
        raise ConfigEntryNotReady

    json = await result.json()
    households = json.get("households")

    async def async_get_available_players(household):
        url = f"https://api.ws.sonos.com/control/api/v1/households/{household}/groups"
        result = await session.async_request("get", url)
        if result.status >= 400:
            body = await result.text()
            _LOGGER.error(
                "Requesting devices failed (%s): %s",
                result.status,
                body,
            )
            raise ConfigEntryNotReady

        json = await result.json()
        _LOGGER.debug("Result: %s", json)
        all_players = json["players"]
        available_players = []

        for player in all_players:
            if "AUDIO_CLIP" in player["capabilities"]:
                available_players.append(player)
            else:
                _LOGGER.warning(
                    "%s (%s) does not support AUDIO_CLIP", player["name"], player["id"]
                )

        return available_players

    for household in households:
        household_id = household["id"]
        players = await async_get_available_players(household_id)
        _LOGGER.debug(
            "Adding players for household %s: %s",
            household_id,
            [player["name"] for player in players],
        )
        hass.data[DOMAIN][PLAYERS].extend(players)

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(PLAYERS)
        hass.data[DOMAIN].pop(SESSION)

    return unload_ok
