# Functions for interacting with Spotify API using Spotipy
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ..secrets import Secrets

# TODO: Implement oauth2 for user authentication
scope = "ugc-image-upload user-follow-modify playlist-modify-private playlist-modify-public user-library-modify playlist-read-collaborative user-read-currently-playing user-follow-read user-read-playback-position user-read-playback-state playlist-read-private user-read-recently-played user-top-read user-read-email user-library-read user-read-private app-remote-control streaming user-modify-playback-state"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=Secrets.CLIENT_ID,
        client_secret=Secrets.CLIENT_SECRET,
        scope=scope,
        redirect_uri="http://127.0.0.1:8080",
        requests_timeout=10,
    )
)

# -------------------- FUNCTIONS --------------------
def get_current_user():
    try:
        print("Getting user")
        user = sp.current_user()
    except spotipy.oauth2.SpotifyOauthError as e:
        print("Error getting User from Spotify!")
    return user

def fetch_all_items(sp, initial_results):
    items = initial_results["items"]
    while initial_results["next"]:
        try:
            initial_results = sp.next(initial_results)
            items.extend(initial_results["items"])
        except Exception as e:
            print(e)
            break
    return items

def get_all_current_user_playlists():
    try:
        initial_results = sp.current_user_playlists()
        playlists = fetch_all_items(sp, initial_results)
    except Exception as e:
        print(e)
        print("You're getting rate limited brah")
    return playlists