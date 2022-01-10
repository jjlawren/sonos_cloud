"""Support to interface with Sonos players."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    ATTR_MEDIA_EXTRA,
    SUPPORT_PLAY_MEDIA,
)
from homeassistant.components.sonos.const import DOMAIN as SONOS_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PLAYERS, SESSION

_LOGGER = logging.getLogger(__name__)

ATTR_VOLUME = "volume"

AUDIO_CLIP_URI = "https://api.ws.sonos.com/control/api/v1/players/{device}/audioClip"


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sonos cloud from a config entry."""
    async_add_entities(
        [SonosCloudMediaPlayerEntity(player) for player in hass.data[DOMAIN][PLAYERS]]
    )


class SonosCloudMediaPlayerEntity(MediaPlayerEntity):
    """Representation of a Sonos Cloud entity."""

    def __init__(self, player: dict[str, Any]):
        """Initializle the entity."""
        self._attr_name = player["name"]
        self._attr_unique_id = player["id"]
        self.zone_devices = player["deviceIds"]

    @property
    def state(self) -> str:
        """Return the state of the entity."""
        return STATE_IDLE

    @property
    def supported_features(self) -> int:
        """Flag media player features that are supported."""
        return SUPPORT_PLAY_MEDIA

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        return DeviceInfo(
            identifiers={(SONOS_DOMAIN, self.unique_id)},
            manufacturer="Sonos",
            name=self.name,
        )

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """
        Send the play_media command to the media player.

        Used to play audio clips over the currently playing music.
        """
        data = {
            "name": "HA Audio Clip",
            "appId": "jjlawren.home-assistant.sonos_cloud",
        }
        devices = [self.unique_id]
        _LOGGER.info("Playing %s", media_id)

        if extra := kwargs.get(ATTR_MEDIA_EXTRA):
            if extra.get("play_on_bonded"):
                devices = self.zone_devices
            if volume := extra.get(ATTR_VOLUME):
                _LOGGER.info("Type of %s: %s", volume, type(volume))
                if type(volume) not in (int, float):
                    raise HomeAssistantError(f"Volume '{volume}' not a number")
                if not 0 < volume <= 100:
                    raise HomeAssistantError(f"Volume '{volume}' not in acceptable range of 0-100")
                if volume < 1:
                    volume = volume * 100
                data[ATTR_VOLUME] = int(volume)
        if media_id != "CHIME":
            data["streamUrl"] = media_id

        session = self.hass.data[DOMAIN][SESSION]
        requests = []

        for device in devices:
            url = AUDIO_CLIP_URI.format(device=device)
            requests.append(session.async_request("post", url, json=data))
        results = await asyncio.gather(*requests, return_exceptions=True)
        for result in results:
            json = await result.json()
            _LOGGER.debug("Response for %s: %s", result.url, json)
