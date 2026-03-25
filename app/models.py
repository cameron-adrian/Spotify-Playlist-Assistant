from django.db import models


class Playlist(models.Model):
    class Meta:
        ordering = ["name"]

    # Spotify fields
    spotify_id = models.CharField(max_length=255, unique=True, primary_key=True)
    name = models.CharField(max_length=100, null=True)
    description = models.TextField(blank=True, default="")
    collaborative = models.BooleanField(null=True)
    public = models.BooleanField(null=True)
    snapshot_id = models.CharField(max_length=100, null=True)
    image_url = models.URLField(blank=True, default="")
    external_url = models.URLField(blank=True, default="")
    owner_id = models.CharField(max_length=255, blank=True, default="")

    # Aggregates (pre-calculated during sync)
    number_of_tracks = models.IntegerField(default=0)
    total_duration = models.IntegerField(default=0)  # seconds
    average_track_length = models.IntegerField(default=0)  # seconds

    def __str__(self):
        return self.name or self.spotify_id


class Artist(models.Model):
    spotify_id = models.CharField(max_length=255, unique=True, primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Track(models.Model):
    spotify_id = models.CharField(max_length=255, unique=True, primary_key=True)
    name = models.CharField(max_length=500)
    duration_ms = models.IntegerField(default=0)
    artists = models.ManyToManyField(Artist, related_name="tracks")
    external_url = models.URLField(blank=True, default="")

    # Audio features (from Spotify audio-features endpoint)
    acousticness = models.FloatField(null=True, blank=True)
    danceability = models.FloatField(null=True, blank=True)
    energy = models.FloatField(null=True, blank=True)
    instrumentalness = models.FloatField(null=True, blank=True)
    liveness = models.FloatField(null=True, blank=True)
    loudness = models.FloatField(null=True, blank=True)  # dB, typically -60 to 0
    speechiness = models.FloatField(null=True, blank=True)
    tempo = models.FloatField(null=True, blank=True)  # BPM
    valence = models.FloatField(null=True, blank=True)  # 0.0 to 1.0 (sad to happy)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def duration_seconds(self):
        return self.duration_ms // 1000


class PlaylistTrack(models.Model):
    """Through model: a track's membership in a playlist."""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name="playlist_tracks")
    track = models.ForeignKey(Track, on_delete=models.CASCADE, related_name="playlist_tracks")
    position = models.IntegerField(default=0)
    added_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["position"]
        unique_together = [("playlist", "track", "position")]

    def __str__(self):
        return f"{self.playlist.name} - {self.track.name} (#{self.position})"
