from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="app"),
    path("playlist/<str:id>/", views.playlist, name="playlist"),
    path("debug", views.debug, name="debug"),
]
