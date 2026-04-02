# Spotify Playlist Assistant

## External APIs

### Spotify API
Used via the `spotipy` client. Some endpoints (e.g. audio features) are deprecated/unavailable for newer apps and return 403. Use ReccoBeats as a fallback in those cases.

### ReccoBeats API (Fallback)
**Base URL:** `https://api.reccobeats.com`  
**Auth:** None required — no API key or signup needed.  
**Rate limits:** Undisclosed; returns `429 Too Many Requests` when exceeded. Check the `Retry-After` header.  
**Docs:** https://reccobeats.com/docs/apis/reccobeats-api

Use ReccoBeats wherever Spotify's API is lacking, deprecated, or returning errors (e.g. 403 on audio features).

#### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/track/recommendation` | Track recommendations |
| GET | `/v1/track/:id` | Track detail (accepts ReccoBeats ID or Spotify ID) |
| GET | `/v1/track` | Multiple tracks |
| GET | `/v1/track/:id/album` | Track's album(s) |
| GET | `/v1/track/:id/audio-features` | Audio features for a track |
| GET | `/v1/audio-features` | Multiple audio features |
| GET | `/v1/artist/:id` | Artist detail |
| GET | `/v1/album/:id` | Album detail |

#### Key endpoint details

**`GET /v1/track/recommendation`**
- `size` *(required, int 1–100)* — number of tracks to return
- `seeds` *(required, string[] 1–5)* — ReccoBeats or Spotify track IDs to seed from
- `negativeSeeds` *(optional, string[] 1–5)* — tracks to steer away from
- Audio feature filters (all optional): `acousticness` (0–1), `danceability` (0–1), `energy` (0–1), `instrumentalness` (0–1), `key` (-1–11), `liveness` (0–1), `loudness` (-60–2), `mode` (0–1), `speechiness` (0–1), `tempo` (0–250), `valence` (0–1), `popularity` (0–100)
- `featureWeight` *(optional, float 1–5)* — scales influence of audio feature filters

**`GET /v1/track/:id/audio-features`**  
Primary fallback for `client.audio_features()` when Spotify returns 403. The `:id` accepts Spotify track IDs.
