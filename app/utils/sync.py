"""
Sync service: pulls data from Spotify and updates the local database.
Called explicitly (via refresh button), NOT on every page load.
"""
import logging
from datetime import datetime, timezone

from ..models import Artist, Playlist, PlaylistTrack, Track
from .spotify import sp, fetch_all_items

logger = logging.getLogger(__name__)


def sync_playlists(user_id):
    """
    Pull all playlists owned by user_id from Spotify.
    Skip any playlist whose snapshot_id hasn't changed.
    Returns (synced_count, skipped_count).
    """
    logger.info("Fetching playlists from Spotify for user %s", user_id)
    initial_results = sp.current_user_playlists()
    all_playlists = fetch_all_items(sp, initial_results)

    synced = 0
    skipped = 0

    for sp_playlist in all_playlists:
        if sp_playlist["owner"]["id"] != user_id:
            continue

        spotify_id = sp_playlist["id"]
        snapshot_id = sp_playlist["snapshot_id"]

        # Check if we already have this exact snapshot
        try:
            existing = Playlist.objects.get(spotify_id=spotify_id)
            if existing.snapshot_id == snapshot_id:
                skipped += 1
                continue
        except Playlist.DoesNotExist:
            pass

        # Fetch full playlist details (includes description, images, followers)
        _sync_single_playlist(spotify_id, sp_playlist)
        synced += 1

    logger.info("Sync complete: %d synced, %d unchanged", synced, skipped)
    return synced, skipped


def _sync_single_playlist(spotify_id, sp_playlist_summary):
    """Sync a single playlist: metadata + all tracks."""
    # Get full playlist detail for fields not in the summary
    sp_detail = sp.playlist(spotify_id)

    images = sp_detail.get("images", [])
    image_url = images[0]["url"] if images else ""
    external_urls = sp_detail.get("external_urls", {})

    # Fetch all tracks (handles pagination)
    initial_tracks = sp_detail.get("tracks", {})
    track_items = fetch_all_items(sp, initial_tracks)

    # Calculate aggregates
    total_duration_ms = 0
    valid_track_count = 0
    for item in track_items:
        track_data = item.get("track")
        if track_data and track_data.get("duration_ms"):
            total_duration_ms += track_data["duration_ms"]
            valid_track_count += 1

    total_duration_sec = total_duration_ms // 1000
    avg_track_sec = (total_duration_sec // valid_track_count) if valid_track_count else 0

    # Save/update playlist
    playlist, _ = Playlist.objects.update_or_create(
        spotify_id=spotify_id,
        defaults={
            "name": sp_detail.get("name", ""),
            "description": sp_detail.get("description", ""),
            "collaborative": sp_detail.get("collaborative", False),
            "public": sp_detail.get("public"),
            "snapshot_id": sp_detail.get("snapshot_id", ""),
            "image_url": image_url,
            "external_url": external_urls.get("spotify", ""),
            "owner_id": sp_detail.get("owner", {}).get("id", ""),
            "number_of_tracks": valid_track_count,
            "total_duration": total_duration_sec,
            "average_track_length": avg_track_sec,
        },
    )

    # Sync tracks
    _sync_tracks_for_playlist(playlist, track_items)


def _sync_tracks_for_playlist(playlist, track_items):
    """Replace all PlaylistTrack entries for this playlist with fresh data."""
    # Clear existing entries for this playlist
    PlaylistTrack.objects.filter(playlist=playlist).delete()

    for position, item in enumerate(track_items):
        track_data = item.get("track")
        if not track_data or not track_data.get("id"):
            continue  # skip local files / unavailable tracks

        # Upsert artists
        artist_objs = []
        for sp_artist in track_data.get("artists", []):
            if not sp_artist.get("id"):
                continue
            artist, _ = Artist.objects.update_or_create(
                spotify_id=sp_artist["id"],
                defaults={"name": sp_artist.get("name", "")},
            )
            artist_objs.append(artist)

        # Upsert track
        ext_urls = track_data.get("external_urls", {})
        track, _ = Track.objects.update_or_create(
            spotify_id=track_data["id"],
            defaults={
                "name": track_data.get("name", ""),
                "duration_ms": track_data.get("duration_ms", 0),
                "external_url": ext_urls.get("spotify", ""),
            },
        )
        track.artists.set(artist_objs)

        # Parse added_at
        added_at = None
        raw_added = item.get("added_at")
        if raw_added:
            try:
                added_at = datetime.fromisoformat(raw_added.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        PlaylistTrack.objects.create(
            playlist=playlist,
            track=track,
            position=position,
            added_at=added_at,
        )
