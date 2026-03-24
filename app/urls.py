from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="app"),
    path("playlist/<str:id>/", views.playlist_detail, name="playlist"),
    path("sync/", views.sync, name="sync"),
]
