"""Support to interface with Sonos players."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components import media_source
from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerEntity,
    async_process_play_media_url,
)
from homeassistant.components.media_player.const import (
    ATTR_MEDIA_EXTRA,
    MEDIA_CLASS_DIRECTORY,
    SUPPORT_BROWSE_MEDIA,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_VOLUME_SET,
)
from homeassistant.components.media_player.errors import BrowseError
from homeassistant.components.sonos.const import DOMAIN as SONOS_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_IDLE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

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


class SonosCloudMediaPlayerEntity(MediaPlayerEntity, RestoreEntity):
    """Representation of a Sonos Cloud entity."""

    def __init__(self, player: dict[str, Any]):
        """Initializle the entity."""
        self._attr_name = player["name"]
        self._attr_unique_id = player["id"]
        self._attr_volume_level = 0
        self.zone_devices = player["deviceIds"]

    async def async_added_to_hass(self):
        """Complete entity setup."""
        await super().async_added_to_hass()
        await self.async_restore_states()

    async def async_restore_states(self) -> None:
        """Restore last entity state."""
        if (last_state := await self.async_get_last_state()) is None:
            return

        if volume := last_state.attributes.get("volume_level"):
            self._attr_volume_level = volume

    @property
    def state(self) -> str:
        """Return the state of the entity."""
        return STATE_IDLE

    @property
    def supported_features(self) -> int:
        """Flag media player features that are supported."""
        return SUPPORT_BROWSE_MEDIA | SUPPORT_PLAY_MEDIA | SUPPORT_VOLUME_SET

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device."""
        return DeviceInfo(
            identifiers={(SONOS_DOMAIN, self.unique_id)},
            manufacturer="Sonos",
            name=self.name,
        )

    async def async_set_volume_level(self, volume: float) -> None:
        """Set the volume level."""
        self._attr_volume_level = volume

    async def async_play_media(
        self, media_type: str, media_id: str, **kwargs: Any
    ) -> None:
        """
        Send the play_media command to the media player.

        Used to play audio clips over the currently playing music.
        """
        if media_source.is_media_source_id(media_id):
            media_source_item = await media_source.async_resolve_media(
                self.hass, media_id
            )
            media_id = async_process_play_media_url(self.hass, media_source_item.url)

        data = {
            "name": "HA Audio Clip",
            "appId": "jjlawren.home-assistant.sonos_cloud",
        }
        devices = [self.unique_id]

        if extra := kwargs.get(ATTR_MEDIA_EXTRA):
            if extra.get("play_on_bonded"):
                devices = self.zone_devices
            if volume := extra.get(ATTR_VOLUME):
                if type(volume) not in (int, float):
                    raise HomeAssistantError(f"Volume '{volume}' not a number")
                if not 0 < volume <= 100:
                    raise HomeAssistantError(
                        f"Volume '{volume}' not in acceptable range of 0-100"
                    )
                if volume < 1:
                    volume = volume * 100
                data[ATTR_VOLUME] = int(volume)

        if ATTR_VOLUME not in data and self.volume_level:
            data[ATTR_VOLUME] = int(self.volume_level * 100)

        if media_id != "CHIME":
            data["streamUrl"] = media_id

        session = self.hass.data[DOMAIN][SESSION]
        requests = []

        for device in devices:
            url = AUDIO_CLIP_URI.format(device=device)
            _LOGGER.debug("Playing on %s (%s): %s", self.name, device, data)
            requests.append(session.async_request("post", url, json=data))
        results = await asyncio.gather(*requests, return_exceptions=True)
        for result in results:
            json = await result.json()
            _LOGGER.debug("Response for %s: %s", result.url, json)

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> Any:
        """Implement the websocket media browsing helper."""
        if media_content_id is None:
            return await root_payload(self.hass)

        if media_source.is_media_source_id(media_content_id):
            return await media_source.async_browse_media(
                self.hass, media_content_id, content_filter=media_source_filter
            )

        raise BrowseError(f"Media not found: {media_content_type} / {media_content_id}")


def media_source_filter(item: BrowseMedia):
    """Filter media sources."""
    return item.media_content_type.startswith("audio/")


async def root_payload(
    hass: HomeAssistant,
):
    """Return root payload for Sonos Cloud."""
    children = []

    try:
        item = await media_source.async_browse_media(
            hass, None, content_filter=media_source_filter
        )
        # If domain is None, it's overview of available sources
        if item.domain is None:
            children.extend(item.children)
        else:
            children.append(item)
    except media_source.BrowseError:
        pass

    return BrowseMedia(
        title="Sonos Cloud",
        media_class=MEDIA_CLASS_DIRECTORY,
        media_content_id="",
        media_content_type="root",
        can_play=False,
        can_expand=True,
        children=children,
    )
