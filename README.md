# Sonos Cloud integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

The `sonos_cloud` integration uses the cloud-based [Sonos Control API](https://developer.sonos.com/reference/control-api/) to send [audioClip](https://developer.sonos.com/reference/control-api/audioclip/) commands to speakers. This allows playback of short clips (e.g., alert sounds, TTS messages) on Sonos speakers without interrupting playback. Audio played in this manner will reduce the volume of currently playing music, play the clip on top of the music, and then automatically return the music to its original volume. This is an alternative approach to the current method which requires taking snapshots & restoring speakers with complex scripts and automations.

This API requires audio files to be in `.mp3` or `.wav` format and to have publicly accessible URLs.

# Installation
**Easy**: Use [HACS](https://hacs.xyz) and add the Sonos Cloud Integration.

**Manual**: Place all files from the `sonos_cloud` directory inside your `<HA_CONFIG>/custom_components/sonos_cloud/` directory.

Both methods will require a restart of Home Assistant before you can configure the integration further.

You will need to create an account on the [Sonos Developer site](https://developer.sonos.com), and then create a new Control Integration. Provide a display name and description, provide a Key Name, and save the integration. It is not necessary to set a Redirect URI or callback URL. Save the Key and Secret values for the integration configuration.

# Configuration

Add an entry to your `configuration.yaml` using the Key and Secret from your Sonos app:
```yaml
sonos_cloud:
  client_id: <YOUR_APP_KEY>
  client_secret: <YOUR_APP_SECRET>
```

On the Integrations page in Home Assistant, add a new "Sonos Cloud" integration. You will be redirected to the Sonos website to login with your "normal" Sonos username and password (_not_ your Sonos Developer login). You will receive a prompt saying "Allow <YOUR_APP_NAME> to control your Sonos system". Accept this and the integration will complete configuration.

# Usage

The integration will create new `media_player` entities for each Sonos device in your household. These are created in order to use the `tts.<platform>_say` and `media_player.play_media` services to play the clips.

## Examples

```yaml
service: tts.cloud_say
data:
  entity_id: media_player.front_room
  message: "Hello there"
```

Service calls to `media_player.play_media` can accept an optional `volume` parameter to play the clip at a different volume than the currently playing music:
```yaml
service: media_player.play_media
data:
  entity_id: media_player.kitchen
  media_content_id: https://<unique_cloud_id>.ui.nabu.casa/local/sound_files/doorbell.mp3
  media_content_type: music
  extra:
    volume: 35  # Can be provided as 0-100 or 0.0-0.99. 1 is considered as the lowest value possible and is the same as 0.01
```

A special `media_content_id` of "CHIME" can be used to test the integration using the built-in sound provided by Sonos. This can be useful for validation if your own URLs are not playing correctly:
```yaml
service: media_player.play_media
data:
  entity_id: media_player.kitchen
  media_content_id: CHIME
  media_content_type: music
```

# Limitations

Audio clips must be publicly accessible. If serving files from your Home Assistant instance (e.g., from the `/www/` config directory or via TTS integrations), the base URLs must be reachable from outside your network. This is easiest when using a Nabu Casa cloud URL.

For example, to configure the `cloud` TTS integration to use external URLs:
```yaml
tts:
  - platform: cloud
    base_url: 'https://<unique_cloud_id>.ui.nabu.casa'
    language: en-US
    gender: female
```
