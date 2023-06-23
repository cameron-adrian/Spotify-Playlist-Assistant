# from django.shortcuts import render
# # from django.http import HttpResponse
# import spotipy
# from spotipy.oauth2 import SpotifyOAuth

# scope = "user-library-read"

# # very nooby auth for my very own spotify account
# sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='c069f0ce51434241be88a7a0891093b5',
#                      client_secret='27ab04ece55349e4b4f74166ba24e3cc', scope=scope, redirect_uri='https://test.com'))


# # I think I see how I'll need a model for this. Fill out some of the attributes with spotipy and the rest myself?
# playlists = [
#     {'id': 1, 'name': 'Party Songs'},
#     {'id': 2, 'name': 'Sad Songs'},
#     {'id': 3, 'name': 'Fun Songs'},
# ]


# def home(request):
#     context = {
#         'playlists': playlists
#     }
#     return render(request, 'home.html', context)
