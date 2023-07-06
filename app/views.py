# Django Setup
from django.shortcuts import render
from .models import Playlist

from .secrets import Secrets

# set up Pretty Printer
import pprint

pp = pprint.PrettyPrinter(indent=4)

# import time
from datetime import timedelta

# import requests

# from urllib import HTTPError
# from ratelimit import limits, RateLimitException, sleep_and_retry
# from backoff import on_exception, expo

# Spotify Stuff
import spotipy
from spotipy.oauth2 import SpotifyOAuth

scope = "ugc-image-upload user-follow-modify playlist-modify-private playlist-modify-public user-library-modify playlist-read-collaborative user-read-currently-playing user-follow-read user-read-playback-position user-read-playback-state playlist-read-private user-read-recently-played user-top-read user-read-email user-library-read user-read-private app-remote-control streaming user-modify-playback-state"


# AUTH_URL = "https://accounts.spotify.com/api/token"

# auth_response = requests.post(
#     AUTH_URL,
#     {
#         "grant_type": "client_credentials",
#         "client_id": CLIENT_ID,
#         "client_secret": CLIENT_SECRET,
#     },
# )

# # convert the response to JSON
# auth_response_data = auth_response.json()

# # save the access token
# access_token = auth_response_data["access_token"]

# headers = {"Authorization": "Bearer {token}".format(token=access_token)}

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


# def get_user():
#     try:
#         print("Getting user")
#         user = sp.current_user()
#     except spotipy.oauth2.SpotifyOauthError as e:
#         print("Error getting User from Spotify!")

# def get_current_user_playlists():
#     try:
#         results = sp.current_user_playlists()
#     except Exception as e:
#         print(e)
#         print("You're getting rate limited brah")

#     playlists = results["items"]

#     while results["next"]:
#         try:
#             print("Trying to get the next page of playlists")
#             results = sp.next(results)
#         except Exception as e:
#             print(e)
#         else:
#             playlists.extend(results["items"])
#     print("Done getting playlist pages")


def save_playlist_to_db(spotify_id, snapshot_id, name, collaborative, public):
    try:
        result = sp.playlist_items(playlist_id=spotify_id)
    except Exception as e:
        print(e)
    else:
        tracks = result["items"]

    while result["next"]:
        try:
            result = sp.next(result)
        except Exception as e:
            print(e)
        else:
            tracks.extend(result["items"])

    # Calculate Total Playlist Duration in Seconds
    total_duration = (
        sum(
            item["track"]["duration_ms"] for item in tracks if item["track"] is not None
        )
    ) / 1000

    # Calculate Average Song Length
    if total_duration:
        average_song_length = round(total_duration / len(result["items"]), 0)
    else:
        average_song_length = None

    pl = Playlist(
        spotify_id=spotify_id,
        snapshot_id=snapshot_id,
        name=name,
        collaborative=collaborative,
        public=public,
        total_duration=total_duration,
        average_song_length=average_song_length,
    )

    pl.save()
    print("Playlist saved")


# -------------------- VIEWS --------------------
def debug(request):
    # r = requests.get("https://api.spotify.com/v1/me/playlists", headers=headers)
    # r = r.json()
    # pp.pprint(r.status_code)
    # pp.pprint(r.text)

    # try:
    #     print("Getting user")
    #     user = sp.current_user()
    # except spotipy.oauth2.SpotifyOauthError as e:
    #     print(e.error_description)

    try:
        print("Getting user")
        user = sp.current_user()
    except Exception as e:
        print(e)

    # test_playlist = sp.playlist(playlist_id="1NN2n3H5ghsl9p2u5kpokf")
    # test_playlist = "a playlist"

    # test_playlists = sp.current_user_playlists(limit=3)
    # test_playlists = "a buncha playlists"

    try:
        top_artists = sp.current_user_top_artists(
            limit=20, offset=0, time_range="medium_term"
        )

    except spotipy.client.SpotifyException as e:
        print(e)

    context = {
        # "test_playlist": test_playlist,
        # "test_playlists": test_playlists,
        "top_artists": top_artists,
    }
    return render(request, "app/debug.html", context)


# Home page that shows all the playlists
def home(request):
    # Database sync update check thing
    try:
        print("Getting user")
        user = sp.current_user()
    except spotipy.oauth2.SpotifyOauthError as e:
        print("Error getting User from Spotify!")

    # maybe don't store everything? Just all the URIs or IDs for each playlist to then make calls later?

    # Get User's Current Playlists
    try:
        results = sp.current_user_playlists()
    except Exception as e:
        print(e)
        print("You're getting rate limited brah")

    playlists = results["items"]

    while results["next"]:
        try:
            # print("Trying to get the next page of playlists")
            results = sp.next(results)
        except Exception as e:
            print(e)
        else:
            playlists.extend(results["items"])
    # ------------------------------------------------------------
    print("Done getting playlist pages")

    # Saving Playlist Data/Calculations to the DB
    print("Starting to save playlists to the database")
    for playlist in playlists:
        spotify_id = playlist["id"]
        snapshot_id = playlist["snapshot_id"]
        name = playlist["name"]
        collaborative = bool(playlist["collaborative"])
        public = bool(playlist["public"])

        # IF snapshot_id in Database equals the snapshot_id of the playlist we just pulled, skip to the next

        try:
            p = Playlist.objects.get(spotify_id=spotify_id)
            if snapshot_id == p.snapshot_id:
                # print("Updated playlist already exists in database, no update needed")
                continue
            else:
                save_playlist_to_db(
                    spotify_id, snapshot_id, name, collaborative, public
                )
                print(f'Playlist "{p.name}" updated to latest snapshot')
        except:
            save_playlist_to_db(spotify_id, snapshot_id, name, collaborative, public)
            # print(f'New playlist "{p.name}" saved to DB')

    playlists = Playlist.objects.all()

    context = {"user": user, "playlists": playlists}
    return render(request, "app/home.html", context)


# An individual Playlist's page
def playlist(request, id):
    # Get Playlist from Database
    playlist = Playlist.objects.get(spotify_id=id)
    # or should I get it from Spotify instead? Probably not cuz I already got all the track items

    # Created At
    # created_at = playlist["tracks"][]

    # Updated At
    # updated_at = playlist["tracks"]["items"]

    # Select the time that the playlist is supposed to start playing
    # Show at what time each song will play

    # Need to actually implement this in some way? Don't honestly know what it should be
    # if request.method == "POST":
    #     pass

    context = {"playlist": playlist}
    return render(request, "app/playlist.html", context)
