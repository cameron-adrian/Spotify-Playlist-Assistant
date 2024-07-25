from django.db import models
from django.urls import reverse

# Create your models here.

# KEEP FILLING ALL OF THESE OUT FROM THE SPOTIFY RESOURCES WHEN FEELING DUMB/LOW BRAIN ENERGY


# User Stats?
# class User(models.Model):
#     # https://developer.spotify.com/documentation/web-api/reference/get-current-users-profile

#     name = models.CharField(max_length=30, null=False)

#     def __str__(self):
#         # """String for representing the User object (in Admin site etc.)."""
#         return self.name


# What if it was called playlist stats? Like only my calculations
class Playlist(models.Model):
    #     # Metadata
    class Meta:
        ordering = ["name"]

    # created_at = models.DateTimeField(auto_now_add=True) TODO: This isn't technically possible, you can only get when the first song was ADDED
    # updated_at = models.DateTimeField(auto_now=True)

    # https://developer.spotify.com/documentation/web-api/reference/get-playlist
    name = models.CharField(max_length=100, null=True)
    spotify_id = models.CharField(
        max_length=255, unique=True, blank=False, null=False, primary_key=True
    )
    collaborative = models.BooleanField(null=True)
    public = models.BooleanField(null=True)
    snapshot_id = models.CharField(max_length=100, null=True)

    # My calculations
    average_track_length = models.SmallIntegerField(null=True)
    total_duration = models.SmallIntegerField(null=True)
    number_of_tracks = models.SmallIntegerField(null=True)

    #     # Methods
    #     def get_absolute_url(self):
    #         """Returns the URL to access a particular instance of Playlist."""
    #         return reverse('model-detail-view', args=[str(self.id)])

    # These come from Spotify, may not actually use them?
    # description = models.TextField(max_length=300, null=True, blank=True)

    # followers = models.PositiveIntegerField()
    # href = models.URLField()
    # images = models.ImageField(height_field=, width_field=) Maybe don't even use this one and just ask Spotipy every time? Or Cache? idk
    # owner = This is a reference to another Model, right? A User Model?

    # tracks = models.ManyToManyField("app.Model", verbose_name=_("tracks")) >>> a track can be on many playlists, many playlists can have the same track

    def __str__(self):
        # """String for representing the Playlist object (in Admin site etc.)."""
        return self.name


# class Track(models.Model):
#     name = models.CharField(
#         max_length=200, help_text='This should be the name of the playlist')

#     def __str__(self):
#         # """String for representing the Track object (in Admin site etc.)."""
#         return self.name
