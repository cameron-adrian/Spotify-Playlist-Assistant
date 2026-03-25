from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Playlist, PlaylistTrack
from .utils.spotify import sp, get_current_user
from .utils.sync import sync_playlists


VALID_SORT_FIELDS = {"name", "number_of_tracks", "average_track_length", "total_duration"}


def home(request):
    """List all playlists from the database. No Spotify API calls."""
    playlists = Playlist.objects.all()

    # Sorting
    sort_by = request.GET.get("sort_by", "name")
    order = request.GET.get("order", "asc")
    if sort_by not in VALID_SORT_FIELDS:
        sort_by = "name"
    order_prefix = "-" if order == "desc" else ""
    playlists = playlists.order_by(f"{order_prefix}{sort_by}")

    # Filtering by playlist type
    playlist_type = request.GET.get("type")
    if playlist_type == "collaborative":
        playlists = playlists.filter(collaborative=True)
    elif playlist_type == "public":
        playlists = playlists.filter(public=True)
    elif playlist_type == "private":
        playlists = playlists.filter(public=False, collaborative=False)

    paginator = Paginator(playlists, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "sort_by": sort_by,
        "order": order,
        "playlist_type": playlist_type or "all",
    }
    return render(request, "app/home.html", context)


def playlist_detail(request, id):
    """Show a single playlist and its tracks. No Spotify API calls."""
    playlist = get_object_or_404(Playlist, spotify_id=id)

    # Get tracks through the PlaylistTrack join table
    playlist_tracks = (
        PlaylistTrack.objects
        .filter(playlist=playlist)
        .select_related("track")
        .prefetch_related("track__artists")
    )

    # Sorting tracks
    sort_by = request.GET.get("sort_by", "position")
    order = request.GET.get("order", "asc")
    order_prefix = "-" if order == "desc" else ""

    sort_map = {
        "position": "position",
        "name": "track__name",
        "artist": "track__artists__name",
        "duration": "track__duration_ms",
        "added_at": "added_at",
    }
    sort_field = sort_map.get(sort_by, "position")
    playlist_tracks = playlist_tracks.order_by(f"{order_prefix}{sort_field}")

    # Compute "will play at" times: cumulative offset from now based on
    # playlist position order, then attach to each track for display.
    now = timezone.now()
    tracks_in_position_order = (
        PlaylistTrack.objects
        .filter(playlist=playlist)
        .select_related("track")
        .order_by("position")
    )
    cumulative_ms = 0
    will_play_at_map = {}  # position -> datetime
    for pt in tracks_in_position_order:
        will_play_at_map[pt.position] = now + timedelta(milliseconds=cumulative_ms)
        cumulative_ms += pt.track.duration_ms

    # Attach will_play_at to the evaluated queryset
    playlist_tracks = list(playlist_tracks)
    for pt in playlist_tracks:
        pt.will_play_at = will_play_at_map.get(pt.position)

    context = {
        "playlist": playlist,
        "playlist_tracks": playlist_tracks,
        "sort_by": sort_by,
        "order": order,
    }
    return render(request, "app/playlist.html", context)


def sync(request):
    """Pull latest data from Spotify and update the database."""
    user = get_current_user()
    synced, skipped = sync_playlists(user["id"])
    # Redirect back to home after sync
    return redirect("app")
