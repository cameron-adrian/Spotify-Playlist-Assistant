"""
Regression tests for the February 2026 Spotify Web API playlist-item migration.

Spotify renamed the playlist item field from `track` to `item` and moved
playlist contents from /playlists/{id}/tracks to /playlists/{id}/items. Both
old names are still populated (the OpenAPI schema marks them
`deprecated: true` rather than removing them), so the sync code has to keep
reading either shape until they are finally dropped.

These tests pin down that contract:

* the sync goes through ``client.playlist_items()`` and never touches the
  deprecated ``tracks`` page embedded in the playlist object;
* both the new (``items[].item``) and deprecated (``items[].track``) response
  shapes produce byte-for-byte identical database state.
"""
from datetime import datetime, timezone
from unittest import mock

from django.test import TestCase

from app.models import Artist, Playlist, PlaylistTrack, Track
from app.utils import sync
from app.utils.sync import _get_track, sync_playlists

NEW_SHAPE = "new"
DEPRECATED_SHAPE = "deprecated"

OWNER_ID = "me"
PLAYLIST_ID = "pl1"
SNAPSHOT_ID = "snap1"
ADDED_AT = "2026-03-01T00:00:00Z"
ADDED_AT_PARSED = datetime(2026, 3, 1, 0, 0, tzinfo=timezone.utc)


def make_track(i):
    """A track object as Spotify returns it inside a playlist item."""
    return {
        "id": f"track{i}",
        "name": f"Track {i}",
        "duration_ms": 200000 + i,
        "artists": [{"id": f"artist{i}", "name": f"Artist {i}"}],
        "external_urls": {"spotify": f"https://open.spotify.com/track/track{i}"},
    }


def make_item(track, shape, added_at=ADDED_AT):
    """Wrap a track in a playlist item using the requested field name."""
    key = "item" if shape == NEW_SHAPE else "track"
    return {key: track, "added_at": added_at}


def make_items_page(tracks, shape, next_url=None):
    return {
        "items": [make_item(t, shape) for t in tracks],
        "next": next_url,
    }


class DeprecatedTracksPageRead(AssertionError):
    """Raised when sync reads the deprecated embedded `tracks` page."""


class PlaylistObject(dict):
    """A playlist object that blows up if the deprecated `tracks` page is read.

    The real playlist payload still embeds the first page of contents under
    `tracks`. Reading it is exactly the behaviour the migration removed, so
    make any attempt to do so a hard failure rather than a silent regression.
    """

    @staticmethod
    def _guard(key):
        if key == "tracks":
            raise DeprecatedTracksPageRead(
                "sync read the deprecated embedded `tracks` page of the playlist "
                "object; it must fetch contents via client.playlist_items() instead"
            )

    def __getitem__(self, key):
        self._guard(key)
        return super().__getitem__(key)

    def get(self, key, default=None):
        self._guard(key)
        return super().get(key, default)


# A decoy page hidden under the trapped `tracks` key. If the guard above is
# ever bypassed, these tracks would show up in the database and fail the
# content assertions too.
DECOY_TRACKS_PAGE = {
    "items": [
        {
            "track": {
                "id": "decoy1",
                "name": "Decoy",
                "duration_ms": 999999,
                "artists": [{"id": "decoyartist", "name": "Decoy Artist"}],
                "external_urls": {},
            },
            "added_at": "1999-01-01T00:00:00Z",
        }
    ],
    "next": None,
    "total": 1,
}


class FakeSpotifyClient:
    """Minimal stand-in for the spotipy client used by the sync service."""

    def __init__(self, shape=NEW_SHAPE, tracks=None, items_pages=None,
                 snapshot_id=SNAPSHOT_ID, owner_id=OWNER_ID):
        self.shape = shape
        self.snapshot_id = snapshot_id
        self.owner_id = owner_id
        if items_pages is None:
            tracks = [make_track(1), make_track(2)] if tracks is None else tracks
            items_pages = [make_items_page(tracks, shape)]
        self.items_pages = items_pages

        # Call recording
        self.playlist_calls = []
        self.playlist_items_calls = []
        self.next_calls = []

    def current_user_playlists(self):
        return {
            "items": [
                PlaylistObject({
                    "id": PLAYLIST_ID,
                    "snapshot_id": self.snapshot_id,
                    "owner": {"id": self.owner_id},
                    "tracks": DECOY_TRACKS_PAGE,
                })
            ],
            "next": None,
        }

    def playlist(self, spotify_id):
        self.playlist_calls.append(spotify_id)
        return PlaylistObject({
            "id": spotify_id,
            "name": "My Playlist",
            "description": "desc",
            "collaborative": False,
            "public": True,
            "snapshot_id": self.snapshot_id,
            "images": [{"url": "https://img/1.jpg"}],
            "external_urls": {
                "spotify": f"https://open.spotify.com/playlist/{spotify_id}"
            },
            "owner": {"id": self.owner_id},
            "tracks": DECOY_TRACKS_PAGE,
        })

    def playlist_items(self, spotify_id, additional_types=("track", "episode")):
        self.playlist_items_calls.append((spotify_id, additional_types))
        return self.items_pages[0]

    def next(self, result):
        self.next_calls.append(result.get("next"))
        index = [p.get("next") for p in self.items_pages].index(result["next"]) + 1
        return self.items_pages[index]

    def playlist_tracks(self, *args, **kwargs):  # pragma: no cover - guard
        raise AssertionError(
            "sync called the deprecated client.playlist_tracks(); it must use "
            "client.playlist_items()"
        )


class SyncTestCase(TestCase):
    """Base case that keeps the audio-features backfill off the network."""

    def setUp(self):
        super().setUp()
        patcher = mock.patch.object(sync, "_fetch_audio_features")
        self.fetch_audio_features = patcher.start()
        self.addCleanup(patcher.stop)


class GetTrackTests(TestCase):
    """`_get_track()` bridges the renamed playlist-item field."""

    def test_prefers_new_item_key_when_both_present(self):
        new = make_track(1)
        deprecated = make_track(2)
        self.assertIs(_get_track({"item": new, "track": deprecated}), new)

    def test_falls_back_to_deprecated_track_key(self):
        deprecated = make_track(2)
        self.assertIs(_get_track({"track": deprecated}), deprecated)

    def test_falls_back_when_item_is_explicitly_null(self):
        deprecated = make_track(2)
        self.assertIs(_get_track({"item": None, "track": deprecated}), deprecated)

    def test_returns_none_when_neither_key_present(self):
        self.assertIsNone(_get_track({"added_at": ADDED_AT}))
        self.assertIsNone(_get_track({}))

    def test_returns_none_when_both_keys_are_null(self):
        self.assertIsNone(_get_track({"item": None, "track": None}))


class SyncPlaylistShapeTests(SyncTestCase):
    """`sync_playlists()` handles the new and deprecated item shapes alike."""

    def _assert_synced_correctly(self, client):
        playlist = Playlist.objects.get(spotify_id=PLAYLIST_ID)
        self.assertEqual(playlist.name, "My Playlist")
        self.assertEqual(playlist.description, "desc")
        self.assertIs(playlist.collaborative, False)
        self.assertIs(playlist.public, True)
        self.assertEqual(playlist.snapshot_id, SNAPSHOT_ID)
        self.assertEqual(playlist.image_url, "https://img/1.jpg")
        self.assertEqual(
            playlist.external_url,
            f"https://open.spotify.com/playlist/{PLAYLIST_ID}",
        )
        self.assertEqual(playlist.owner_id, OWNER_ID)

        # 200001ms + 200002ms -> 400s total, 200s average
        self.assertEqual(playlist.number_of_tracks, 2)
        self.assertEqual(playlist.total_duration, 400)
        self.assertEqual(playlist.average_track_length, 200)

        # Tracks
        self.assertEqual(Track.objects.count(), 2)
        track1 = Track.objects.get(spotify_id="track1")
        self.assertEqual(track1.name, "Track 1")
        self.assertEqual(track1.duration_ms, 200001)
        self.assertEqual(
            track1.external_url, "https://open.spotify.com/track/track1"
        )

        # Artists, and their m2m wiring
        self.assertEqual(Artist.objects.count(), 2)
        self.assertEqual(
            [a.name for a in track1.artists.all()], ["Artist 1"]
        )
        self.assertEqual(
            list(Artist.objects.values_list("spotify_id", flat=True)),
            ["artist1", "artist2"],
        )

        # Membership rows: position and parsed added_at
        rows = list(
            PlaylistTrack.objects.filter(playlist=playlist).order_by("position")
        )
        self.assertEqual([r.track_id for r in rows], ["track1", "track2"])
        self.assertEqual([r.position for r in rows], [0, 1])
        for row in rows:
            self.assertEqual(row.added_at, ADDED_AT_PARSED)

        # Nothing from the deprecated embedded page leaked in
        self.assertFalse(Track.objects.filter(spotify_id="decoy1").exists())

    def test_sync_with_new_item_shape(self):
        client = FakeSpotifyClient(shape=NEW_SHAPE)

        synced, skipped = sync_playlists(client, OWNER_ID)

        self.assertEqual((synced, skipped), (1, 0))
        self._assert_synced_correctly(client)

    def test_sync_with_deprecated_track_shape(self):
        client = FakeSpotifyClient(shape=DEPRECATED_SHAPE)

        synced, skipped = sync_playlists(client, OWNER_ID)

        self.assertEqual((synced, skipped), (1, 0))
        self._assert_synced_correctly(client)

    def test_both_shapes_produce_identical_state(self):
        sync_playlists(FakeSpotifyClient(shape=NEW_SHAPE), OWNER_ID)
        new_state = self._snapshot_db()

        self._reset_db()

        sync_playlists(FakeSpotifyClient(shape=DEPRECATED_SHAPE), OWNER_ID)
        deprecated_state = self._snapshot_db()

        self.assertEqual(new_state, deprecated_state)

    def test_audio_feature_backfill_never_hits_the_network(self):
        sync_playlists(FakeSpotifyClient(shape=NEW_SHAPE), OWNER_ID)

        self.assertTrue(self.fetch_audio_features.called)
        called_ids = set()
        for call in self.fetch_audio_features.call_args_list:
            called_ids.update(call.args[0])
        self.assertEqual(called_ids, {"track1", "track2"})

    def _snapshot_db(self):
        return {
            "playlists": list(
                Playlist.objects.values().order_by("spotify_id")
            ),
            "tracks": list(Track.objects.values().order_by("spotify_id")),
            "artists": list(Artist.objects.values().order_by("spotify_id")),
            "memberships": list(
                PlaylistTrack.objects.values(
                    "playlist_id", "track_id", "position", "added_at"
                ).order_by("playlist_id", "position")
            ),
            "track_artists": sorted(
                Track.objects.values_list("spotify_id", "artists__spotify_id")
            ),
        }

    def _reset_db(self):
        PlaylistTrack.objects.all().delete()
        Playlist.objects.all().delete()
        Track.objects.all().delete()
        Artist.objects.all().delete()


class PlaylistItemsEndpointTests(SyncTestCase):
    """Contents come from /playlists/{id}/items, not the deprecated page."""

    def test_calls_playlist_items_with_track_additional_types(self):
        client = FakeSpotifyClient()

        sync_playlists(client, OWNER_ID)

        self.assertEqual(
            client.playlist_items_calls, [(PLAYLIST_ID, ("track",))]
        )

    def test_does_not_read_the_deprecated_embedded_tracks_page(self):
        # PlaylistObject raises DeprecatedTracksPageRead on any read of the
        # `tracks` key, so a clean sync is the assertion. The decoy content
        # under that key is a second line of defence.
        client = FakeSpotifyClient()

        sync_playlists(client, OWNER_ID)

        self.assertEqual(Track.objects.count(), 2)
        self.assertFalse(Track.objects.filter(spotify_id="decoy1").exists())

    def test_trap_actually_fires_when_the_tracks_page_is_read(self):
        # Guard the guard: prove the trap above can fail.
        playlist_obj = FakeSpotifyClient().playlist(PLAYLIST_ID)

        with self.assertRaises(DeprecatedTracksPageRead):
            playlist_obj["tracks"]
        with self.assertRaises(DeprecatedTracksPageRead):
            playlist_obj.get("tracks", {})

    def test_paginates_through_all_item_pages(self):
        pages = [
            make_items_page([make_track(1)], NEW_SHAPE, next_url="page2"),
            make_items_page([make_track(2)], NEW_SHAPE),
        ]
        client = FakeSpotifyClient(items_pages=pages)

        sync_playlists(client, OWNER_ID)

        self.assertEqual(client.next_calls, ["page2"])
        self.assertEqual(
            list(Track.objects.values_list("spotify_id", flat=True)),
            ["track1", "track2"],
        )
        self.assertEqual(
            Playlist.objects.get(spotify_id=PLAYLIST_ID).number_of_tracks, 2
        )


class SyncSkipTests(SyncTestCase):
    """Snapshot and unusable-item handling on top of the migrated read path."""

    def test_skips_playlist_with_unchanged_snapshot_id(self):
        Playlist.objects.create(
            spotify_id=PLAYLIST_ID, name="Cached", snapshot_id=SNAPSHOT_ID
        )
        client = FakeSpotifyClient()

        synced, skipped = sync_playlists(client, OWNER_ID)

        self.assertEqual((synced, skipped), (0, 1))
        self.assertEqual(client.playlist_items_calls, [])
        self.assertEqual(client.playlist_calls, [])
        self.assertEqual(Playlist.objects.get(spotify_id=PLAYLIST_ID).name, "Cached")

    def test_resyncs_playlist_when_snapshot_id_changed(self):
        Playlist.objects.create(
            spotify_id=PLAYLIST_ID, name="Stale", snapshot_id="old-snapshot"
        )
        client = FakeSpotifyClient()

        synced, skipped = sync_playlists(client, OWNER_ID)

        self.assertEqual((synced, skipped), (1, 0))
        self.assertEqual(client.playlist_items_calls, [(PLAYLIST_ID, ("track",))])
        self.assertEqual(
            Playlist.objects.get(spotify_id=PLAYLIST_ID).name, "My Playlist"
        )

    def test_skips_items_without_a_track_id(self):
        local_file = {
            "id": None,
            "name": "Local File",
            "duration_ms": 0,
            "artists": [],
            "external_urls": {},
        }
        pages = [{
            "items": [
                make_item(make_track(1), NEW_SHAPE),
                make_item(local_file, NEW_SHAPE),
                {"item": None, "added_at": ADDED_AT},   # removed / unavailable
                make_item(make_track(2), NEW_SHAPE),
            ],
            "next": None,
        }]
        client = FakeSpotifyClient(items_pages=pages)

        sync_playlists(client, OWNER_ID)

        self.assertEqual(
            list(Track.objects.values_list("spotify_id", flat=True)),
            ["track1", "track2"],
        )
        playlist = Playlist.objects.get(spotify_id=PLAYLIST_ID)
        self.assertEqual(playlist.number_of_tracks, 2)
        self.assertEqual(playlist.total_duration, 400)
        self.assertEqual(
            list(
                PlaylistTrack.objects.filter(playlist=playlist)
                .order_by("position")
                .values_list("track_id", flat=True)
            ),
            ["track1", "track2"],
        )

    def test_skips_items_without_a_track_id_in_deprecated_shape(self):
        pages = [{
            "items": [
                make_item(make_track(1), DEPRECATED_SHAPE),
                {"track": None, "added_at": ADDED_AT},
            ],
            "next": None,
        }]
        client = FakeSpotifyClient(shape=DEPRECATED_SHAPE, items_pages=pages)

        sync_playlists(client, OWNER_ID)

        self.assertEqual(
            list(Track.objects.values_list("spotify_id", flat=True)), ["track1"]
        )
        self.assertEqual(
            Playlist.objects.get(spotify_id=PLAYLIST_ID).number_of_tracks, 1
        )
