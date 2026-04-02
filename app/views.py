from datetime import timedelta
from functools import wraps

from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Playlist, PlaylistTrack
from .utils.spotify import (
    get_authorize_url,
    exchange_code,
    get_client,
    get_current_user,
)
from .utils.sync import sync_playlists, AUDIO_FEATURE_FIELDS


VALID_SORT_FIELDS = {"name", "number_of_tracks", "average_track_length", "total_duration"}


# ---- Auth helpers ----

def login_required_spotify(view_fn):
    """Redirect to login if no Spotify token is in the session."""
    @wraps(view_fn)
    def wrapper(request, *args, **kwargs):
        if "spotify_token" not in request.session:
            return redirect("login")
        return view_fn(request, *args, **kwargs)
    return wrapper


def _get_spotify_client(request):
    """Build a Spotify client from the session token, refreshing if needed."""
    token_info = request.session["spotify_token"]
    client, token_info = get_client(token_info)
    request.session["spotify_token"] = token_info  # save refreshed token
    return client


# ---- Auth views ----

def login(request):
    """Show login page or redirect already-authenticated users."""
    if "spotify_token" in request.session:
        return redirect("app")
    return render(request, "app/login.html")


def spotify_login(request):
    """Redirect the user to Spotify's authorization page."""
    return redirect(get_authorize_url())


def callback(request):
    """Handle the redirect back from Spotify after authorization."""
    code = request.GET.get("code")
    error = request.GET.get("error")

    if error or not code:
        return redirect("login")

    token_info = exchange_code(code)
    request.session["spotify_token"] = token_info
    return redirect("app")


def logout(request):
    """Clear the session and redirect to login."""
    request.session.flush()
    return redirect("login")


# ---- App views ----

@login_required_spotify
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


@login_required_spotify
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
        "acousticness": "track__acousticness",
        "danceability": "track__danceability",
        "energy": "track__energy",
        "instrumentalness": "track__instrumentalness",
        "liveness": "track__liveness",
        "loudness": "track__loudness",
        "speechiness": "track__speechiness",
        "tempo": "track__tempo",
        "valence": "track__valence",
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

    # Compute heat map data: for each feature, find min/max across the
    # playlist so we can compute a 0-1 percentile for each track.
    heatmap_features = ["duration_ms"] + AUDIO_FEATURE_FIELDS
    feature_ranges = {}
    has_audio_features = False
    for feat in heatmap_features:
        vals = []
        for pt in playlist_tracks:
            val = getattr(pt.track, feat, None)
            if val is not None:
                vals.append(val)
        if vals:
            min_v, max_v = min(vals), max(vals)
            feature_ranges[feat] = (min_v, max_v)
            if feat in AUDIO_FEATURE_FIELDS:
                has_audio_features = True

    # Attach a heatmap dict to each playlist_track: feature -> 0.0..1.0
    for pt in playlist_tracks:
        pt.heatmap = {}
        for feat, (min_v, max_v) in feature_ranges.items():
            val = getattr(pt.track, feat, None)
            if val is not None and max_v != min_v:
                pt.heatmap[feat] = (val - min_v) / (max_v - min_v)
            else:
                pt.heatmap[feat] = 0.5  # no spread = neutral

    # Determine which feature to heat-map (from query param)
    heatmap_by = request.GET.get("heatmap", "")

    context = {
        "playlist": playlist,
        "playlist_tracks": playlist_tracks,
        "sort_by": sort_by,
        "order": order,
        "heatmap_by": heatmap_by,
        "heatmap_features": heatmap_features,
        "audio_features": AUDIO_FEATURE_FIELDS,
        "has_audio_features": has_audio_features,
    }
    return render(request, "app/playlist.html", context)


@login_required_spotify
def sync(request):
    """Pull latest data from Spotify and update the database."""
    client = _get_spotify_client(request)
    user, token_info = get_current_user(request.session["spotify_token"])
    request.session["spotify_token"] = token_info
    synced, skipped = sync_playlists(client, user["id"])
    return redirect("app")
