# Sonos Cloud integration for [Home Assistant](https://www.home-assistant.io)

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

The `sonos_cloud` integration uses the cloud-based [Sonos Control API](https://docs.sonos.com/docs/control) to send [audioClip](https://docs.sonos.com/reference/audioclip-loadaudioclip-playerid) commands to speakers. This allows playback of short clips (e.g., alert sounds, TTS messages) on Sonos speakers without interrupting playback. Audio played in this manner will reduce the volume of currently playing music, play the clip on top of the music, and then automatically return the music to its original volume. This is an alternative approach to the current method which requires taking snapshots & restoring speakers with complex scripts and automations.

This API requires audio files to be in `.mp3` or `.wav` format and to have publicly accessible URLs.

# Installation
**Easy**: Use [HACS](https://hacs.xyz) and add the Sonos Cloud Integration.

**Manual**: Place all files from the `sonos_cloud` directory inside your `<HA_CONFIG>/custom_components/sonos_cloud/` directory.

Both methods will require a restart of Home Assistant before you can configure the integration further.

You will need to create an account on the [Sonos Developer site](https://developer.sonos.com), and then create a new Control Integration. Provide a display name and description, provide a Key Name, and save the integration. It is not necessary to set a Redirect URI or callback URL. Save the Key and Secret values for the integration configuration.

# Configuration
<details>
  <summary><i>** Click here if using Home Assistant 2022.5 or below **</i></summary>
  <hr/>
  Older versions of Home Assistant do not support setting application credentials in the frontend.

  Add an entry to your `configuration.yaml` using the Key and Secret from your Sonos app:
  ```yaml
  sonos_cloud:
    client_id: <YOUR_APP_KEY>
    client_secret: <YOUR_APP_SECRET>
  ```
  You will need to restart Home Assistant if adding credentials while already running.

  **Note**: This is no longer necessary in 2022.6 and later with Sonos Cloud release 0.3.0.
  <hr/>
</details>

[![Open your Home Assistant instance and start setting up sonos_cloud.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=sonos_cloud)

On the Integrations page in Home Assistant, add a new "Sonos Cloud" integration. You will need to first provide your application credentials obtained from the Sonos Developer site above. The Key should be used as the `Client ID`, and the Secret as the `Client Secret`.

You will then be redirected to the Sonos website to login with your "normal" Sonos username and password (_not_ your Sonos Developer login). You will receive a prompt saying "Allow <YOUR_APP_NAME> to control your Sonos system". Accept this and the integration will complete configuration.

# Usage

The integration will create new `media_player` entities for each Sonos device in your household. You must reference these new `media_player` entities in order to use the `tts.<platform>_say` and `media_player.play_media` services to play the clips.

## Media Browser & Media Source

Support for browsing and playing back local audio clips using the Media Browser is supported. [Media Source](https://www.home-assistant.io/integrations/media_source/) URLs for local media and TTS can also be provided to `media_player.play_media`.

## Volume control

The playback volume can be set per audio clip and will automatically revert to the previous level when the clip finishes playing. The volume used is chosen in the following order:
1. Use `data`->`extra`->`volume` if provided in the `media_player.play_media` call.
2. Use the volume on the `media_player` entity created by this integration. This default can be disabled by setting the volume slider back to 0. Note that this volume slider _only_ affects the default audio clip playback volume.
3. If neither of the above is provided, the current volume set on the speaker will be used.

**Note**: Volume adjustments only work with the `media_player.play_media` service call. For TTS volume control, use `media_player.play_media` with a [Media Source](https://www.home-assistant.io/integrations/media_source/) TTS URL (see below).

# Examples

Service calls to `media_player.play_media` can accept optional parameters under `data`->`extra`:
* `volume` will play the clip at a different volume than the currently playing music
* `play_on_bonded` will play on all _bonded_ speakers in a "room" (see [notes](#home-theater--stereo-pair-configurations) below)
```yaml
service: media_player.play_media
data:
  entity_id: media_player.kitchen
  media_content_id: https://<unique_cloud_id>.ui.nabu.casa/local/sound_files/doorbell.mp3
  media_content_type: music
  extra:
    volume: 35  # Can be provided as 0-100 or 0.0-0.99
    play_on_bonded: true
```

[Media Source](https://www.home-assistant.io/integrations/media_source/) URLs are supported:
```yaml
service: media_player.play_media
data:
  entity_id: media_player.kitchen
  media_content_id: media-source://media_source/local/doorbell.mp3
  media_content_type: music
```

TTS volume controls can be used with a Media Source TTS URL:
```yaml
service: media_player.play_media
data:
  entity_id: media_player.kitchen
  media_content_id: media-source://tts/cloud?message=I am very loud
  media_content_type: music
  extra:
    volume: 80
```

"Standard" TTS service calls can also be used, but the extra parameters cannot be used:
```yaml
service: tts.cloud_say
data:
  entity_id: media_player.front_room
  message: "Hello there"
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

If you encounter issues playing audio when using this integration, it may be related to one of the following reasons.

## Use the new Sonos entities

If audio playback does not resume after playing a sound, you may have selected the incorrect entity. The integration will create new `media_player` entities for each Sonos device in your household. You must select these new entities as the target for playback, not the original entities.

## Device support

Some device models may not support the `audioClip` feature or will only provide limited support. For example, some older models on S1 firmware may not support this feature at all. A warning message will be logged during startup for each unsupported device. Other speakers (e.g., Play:1 speakers) may support a stripped-down version of the feature which does not overlay the alert audio on top of playing music, but instead will pause/resume the background audio.

## Home theater & stereo pair configurations

A stereo pair will only play back audio on the left speaker and a home theater setup will play from the "primary" speaker. This is because of a limitation in the API which can only target a single speaker device at a time.

When using the `play_on_bonded` extra key, the integration will attempt to play the audio on all bonded speakers in a "room" by making multiple simultaneous calls. Since playback may not be perfectly synchronized with this method it is not enabled by default.

## Media URLs

If serving files from your Home Assistant instance (e.g., from the `/www/` config directory or via TTS integrations), the URLs must be resolvable and directly reachable from the Sonos speakers.

### TTS

To configure TTS integrations to use external URLs, set the `base_url` configuration option.

Examples:
```yaml
tts:
  - platform: cloud
    base_url: 'https://<unique_cloud_id>.ui.nabu.casa'
    language: en-US
    gender: female
```
or
```yaml
tts:
  - platform: google_translate
    base_url: 'https://xxxxxx.duckdns.org:8123'
```

## Secure connections

Sonos devices have strict security requirements if served media over an SSL/TLS connection. [See more details here](https://docs.sonos.com/docs/security).
