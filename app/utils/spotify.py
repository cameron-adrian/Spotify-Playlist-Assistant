"""
Spotify API helpers using Spotipy with session-based OAuth.

Instead of a global cached client, each request builds a Spotify client
from the access token stored in the Django session.
"""
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


def _get_oauth_manager():
    """Build a SpotifyOAuth manager (stateless — no token cache)."""
    return SpotifyOAuth(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=os.environ.get(
            "SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/callback"
        ),
        scope=SCOPE,
        cache_handler=spotipy.MemoryCacheHandler(),
    )


def get_authorize_url():
    """Return the Spotify authorize URL the user should be redirected to."""
    oauth = _get_oauth_manager()
    return oauth.get_authorize_url()


def exchange_code(code):
    """Exchange an authorization code for a token dict.

    Returns a dict with access_token, refresh_token, expires_at, etc.
    """
    oauth = _get_oauth_manager()
    return oauth.get_access_token(code, as_dict=True, check_cache=False)


def refresh_token(token_info):
    """Refresh an expired token. Returns updated token dict."""
    oauth = _get_oauth_manager()
    return oauth.refresh_access_token(token_info["refresh_token"])


def get_client(token_info):
    """Build a Spotify client from a token dict (stored in the session)."""
    oauth = _get_oauth_manager()
    # Let spotipy handle token refresh automatically
    if oauth.is_token_expired(token_info):
        token_info = refresh_token(token_info)
    return spotipy.Spotify(auth=token_info["access_token"]), token_info


def get_current_user(token_info):
    """Return the current user's profile dict."""
    client, token_info = get_client(token_info)
    logger.info("Getting current user from Spotify")
    return client.current_user(), token_info


def fetch_all_items(client, initial_results):
    """Page through all results from a Spotify list endpoint."""
    items = initial_results["items"]
    while initial_results["next"]:
        try:
            initial_results = client.next(initial_results)
            items.extend(initial_results["items"])
        except Exception as e:
            logger.error("Error fetching next page: %s", e)
            break
    return items
