# Spotify Playlist Assistant

## External APIs

### Spotify API

Used via the `spotipy` client. Two waves of deprecations matter here: **Nov 2024** (audio
features) and **Feb 2026** (playlist shape, `/me` fields, batch endpoints). PR #5 (`7316922`)
migrated the code to the Feb 2026 shape.

#### Reading the schema

The OpenAPI schema is the authority on what exists:
`https://developer.spotify.com/reference/web-api/open-api-schema.yaml`

That domain is often blocked by egress proxies. A byte-identical mirror lives at
`https://raw.githubusercontent.com/sonallux/spotify-web-api/main/official-spotify-open-api.yml`
(md5 `c178c88a902f15df2024138a806ff10d`).

**Spotify deprecates rather than deletes.** Retired endpoints and fields stay in the schema
marked `deprecated: true`. A path being present does *not* mean it is usable — `/audio-features`
is still listed and still 403s for new apps. Always check the `deprecated` flag, not just
presence.

#### Feb 2026 renames

Old names are deprecated but still populated, so read the new name and fall back.

| Old | New |
|-----|-----|
| `PlaylistObject.tracks` | `PlaylistObject.items` |
| `PlaylistTrackObject.track` | `PlaylistTrackObject.item` |
| `GET /playlists/{id}/tracks` | `GET /playlists/{id}/items` |
| `POST /users/{user_id}/playlists` | `POST /me/playlists` |
| `PUT`/`DELETE /me/tracks`, `/me/albums`, `/me/following` | `PUT`/`DELETE /me/library` |

Playlist contents are only returned for playlists the current user **owns or collaborates on**.
Others return metadata only, and `403` on items. `SimplifiedPlaylistObject` carries the same
`tracks` → `items` rename.

#### Deprecated fields

| Object | Deprecated |
|--------|-----------|
| `PrivateUserObject` (`GET /me`) | `country`, `email`, `product`, `explicit_content`, `followers` |
| `TrackObject` | `popularity`, `available_markets`, `preview_url`, `external_ids`, `linked_from` |

`PrivateUserObject` gained **`account_id`** — a stable, immutable pseudoanonymous identifier.
The schema says to prefer it over `id` for account linking (`id` can change).

Because `GET /me` is the only endpoint declaring them, the `user-read-email` and
`user-read-private` scopes were dropped from `app/utils/spotify.py`.

#### Endpoint status

| Still current | Deprecated |
|---------------|-----------|
| `GET /me`, `GET /me/playlists` | `GET /users/{user_id}`, `GET /users/{user_id}/playlists` |
| `GET /playlists/{id}`, `GET /playlists/{id}/items` | `GET /playlists/{id}/tracks` |
| `GET /search` | `/recommendations`, `/browse/*`, `/markets` |
| `GET /tracks/{id}`, `/artists/{id}`, `/albums/{id}` | batch `GET /tracks`, `/artists`, `/albums` |
| | `/artists/{id}/top-tracks`, `/artists/{id}/related-artists` |

Note the pattern: **single-object lookups survived, the batch forms did not.** Fetching N tracks
now means N requests.

`GET /search`: `limit` maximum is now **10** (default 5), down from 50/20.

#### Access requirements

Not in the schema — from Spotify's [Feb 2026](https://developer.spotify.com/blog/2026-02-06-update-on-developer-access-and-platform-security)
and [Jul 2026](https://developer.spotify.com/blog/2026-07-23-web-api-quota-updates) announcements.

- The account registering the app must hold an **active Spotify Premium** subscription.
- Development Mode is capped at **5 test users**.
- July 2026 raised the Client ID cap to **25 per developer** (from 1) and moved quota
  accounting to **per-developer-account** rather than per-Client-ID — all Dev Mode apps share
  one budget.
- Extended Quota Mode — the only route back to the deprecated endpoints — requires a registered
  business and 250k MAU. **Out of reach for this project**, so treat deprecated endpoints as
  permanently unavailable rather than something to apply for.

#### spotipy

`requirements.txt` pins `spotipy>=2.26.0`. 2.26.0 (2026-03-03) is the first release whose
`playlist_items()` calls `/items` rather than `/tracks`.

**spotipy passes raw JSON through — it does not normalize the renamed fields.** Callers must
handle `item` vs `track` themselves; see `_get_track()` in `app/utils/sync.py`.

Some 2.26.0 methods still target deprecated paths:

| Method | Hits | Use instead |
|--------|------|-------------|
| `user_playlist_create()` | `POST /users/{user}/playlists` | `current_user_playlist_create()` |
| `user_playlists()` | `GET /users/{user}/playlists` | `current_user_playlists()` |

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
