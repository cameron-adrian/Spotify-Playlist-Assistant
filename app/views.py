# Django Setup
from django.shortcuts import render
from django.core.paginator import Paginator
# Models
from .models import Playlist
# Set up Pretty Printer
import pprint

pp = pprint.PrettyPrinter(indent=4)
# Time Tools
from datetime import timedelta
# Spotify Tools
from .utils.spotify import sp, fetch_all_items, get_all_current_user_playlists, get_current_user
# Database Tools
from .utils.database_tools import save_playlist_to_db

# -------------------- VIEWS --------------------
# Home page that shows all the playlists
def home(request):
    # Get Current User from Spotify
    user = get_current_user()
    # maybe don't store everything? Just all the URIs or IDs for each playlist to then make calls later?

    # Get Current User's Playlists From Spotify
    print("Retrieving all playlists from Spotify")
    playlists = get_all_current_user_playlists()
    print("Done getting playlists from Spotify")

    # Saving Playlist Data/Calculations to the DB
    print("Starting to save playlists to the database")

    
    for playlist in playlists:
        # Check if the playlist is owned by the user, if not, skip to the next one
        if playlist["owner"]["id"] == user["id"]:
            spotify_id = playlist["id"]
            snapshot_id = playlist["snapshot_id"]
            name = playlist["name"]
            collaborative = bool(playlist["collaborative"])
            public = bool(playlist["public"])
            number_of_tracks = playlist["tracks"]["total"]
            print("A:" + str(number_of_tracks))
        
        # IF snapshot_id in Database equals the snapshot_id of the playlist we just pulled, skip to the next playlist
        try:
            p = Playlist.objects.get(spotify_id=spotify_id)
            if snapshot_id == p.snapshot_id:
                # print("Updated playlist already exists in database, no update needed")
                continue
            else:
                print("B:" + str(number_of_tracks))
                save_playlist_to_db(
                    spotify_id, snapshot_id, name, collaborative, public, number_of_tracks
                )
                print(f'Playlist "{p.name}" updated to latest snapshot')
        except:
            print("C:" + str(number_of_tracks))
            save_playlist_to_db(spotify_id, snapshot_id, name, collaborative, public, number_of_tracks)
            print(f'New playlist "{name}" saved to DB')

    # Store all playlists from the database in a variable
    playlists = Playlist.objects.all()

    paginator = Paginator(playlists, 50)  # Show 50 playlists per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "user": user, 
        "playlists": playlists, 
        'page_obj': page_obj, 
        'sort_by': request.GET.get('sort_by', 'name'),
        'order': request.GET.get('order', 'asc')
        }
    return render(request, "app/home.html", context)




# TODO: 2. don't get the user and playlists every time, only when the user logs in or when the user clicks a button to refresh the data


# An individual Playlist's page
def playlist(request, id):

    # Get Playlist from Database if it exists, otherwise get it from Spotify and update the database
    if Playlist.objects.filter(spotify_id=id).exists():
        playlist = Playlist.objects.get(spotify_id=id)
    else:
        playlist = sp.playlist(playlist_id=id)
        save_playlist_to_db(playlist["id"], playlist["snapshot_id"], playlist["name"], playlist["collaborative"], playlist["public"])


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

    # TODO: 1. FIX: Actually store tracks in the database? Or just use the playlist ID to call Spotify every time you click into a playlist?
    # TODO: FEATURE: Add a button to refresh the playlist data

    context = {"playlist": playlist}

    return render(request, "app/playlist.html", context)

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
