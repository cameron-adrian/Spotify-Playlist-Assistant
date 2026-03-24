from django.contrib import admin
from .models import Artist, Playlist, PlaylistTrack, Track

admin.site.register(Playlist)
admin.site.register(Artist)
admin.site.register(Track)
admin.site.register(PlaylistTrack)
