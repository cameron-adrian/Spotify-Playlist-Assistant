# Functions for interacting with Spotify API using Spotipy
import os
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)

SCOPE = (
    "ugc-image-upload user-follow-modify playlist-modify-private playlist-modify-public "
    "user-library-modify playlist-read-collaborative user-read-currently-playing "
    "user-follow-read user-read-playback-position user-read-playback-state "
    "playlist-read-private user-read-recently-played user-top-read user-read-email "
    "user-library-read user-read-private app-remote-control streaming "
    "user-modify-playback-state"
)

_sp = None


def get_spotify_client():
    """Lazy-initialize the Spotify client so imports don't require credentials."""
    global _sp
    if _sp is None:
        _sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.environ["SPOTIFY_CLIENT_ID"],
                client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
                scope=SCOPE,
                redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080"),
                requests_timeout=10,
            )
        )
    return _sp


# Keep `sp` as a lazy proxy for backwards compat
class _SpotifyProxy:
    """Proxy that defers client creation until first attribute access."""
    def __getattr__(self, name):
        return getattr(get_spotify_client(), name)

sp = _SpotifyProxy()


def get_current_user():
    client = get_spotify_client()
    logger.info("Getting current user from Spotify")
    user = client.current_user()
    return user


def fetch_all_items(client, initial_results):
    items = initial_results["items"]
    while initial_results["next"]:
        try:
            initial_results = client.next(initial_results)
            items.extend(initial_results["items"])
        except Exception as e:
            logger.error("Error fetching next page: %s", e)
            break
    return items


def get_all_current_user_playlists():
    client = get_spotify_client()
    initial_results = client.current_user_playlists()
    return fetch_all_items(client, initial_results)
