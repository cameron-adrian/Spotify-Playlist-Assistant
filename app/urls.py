from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="app"),
    path("login/", views.login, name="login"),
    path("login/spotify/", views.spotify_login, name="spotify_login"),
    path("callback/", views.callback, name="callback"),
    path("logout/", views.logout, name="logout"),
    path("playlist/<str:id>/", views.playlist_detail, name="playlist"),
    path("sync/", views.sync, name="sync"),
]
