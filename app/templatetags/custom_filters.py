from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def make_time_readable_hours(duration):
    if duration is None:
        return "N/A"

    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)}h {int(minutes)}m"


@register.filter
def make_time_readable_minutes(duration):
    if duration is None:
        return "N/A"

    minutes, seconds = divmod(duration, 60)
    return f"{int(minutes)}:{int(round(seconds, 0)):02d}"


@register.filter
def heatmap_style(pt, feature):
    """Return inline CSS background color for the heatmap value.

    0.0 = cool (blue/green), 0.5 = neutral (transparent), 1.0 = hot (red/orange).
    """
    heatmap = getattr(pt, "heatmap", None)
    if not heatmap or feature not in heatmap:
        return ""
    t = heatmap[feature]  # 0.0 to 1.0
    # Map to hue: 200 (blue) → 50 (yellow) → 0 (red)
    # and increase saturation/opacity toward extremes
    distance = abs(t - 0.5) * 2  # 0 at center, 1 at extremes
    if t >= 0.5:
        # warm side: red-orange
        hue = int(50 * (1 - (t - 0.5) * 2))  # 50 → 0
    else:
        # cool side: blue-cyan
        hue = int(200 - 80 * t * 2)  # 200 → 120
    saturation = 80
    lightness = 50
    alpha = round(distance * 0.35, 3)  # max 0.35 opacity so text stays readable
    return mark_safe(f'style="background-color: hsla({hue}, {saturation}%, {lightness}%, {alpha})"')


FEATURE_DISPLAY = {
    "duration_ms": "Duration",
    "acousticness": "Acoustic",
    "danceability": "Dance",
    "energy": "Energy",
    "instrumentalness": "Instr.",
    "liveness": "Live",
    "loudness": "Loud",
    "speechiness": "Speech",
    "tempo": "Tempo",
    "valence": "Valence",
}


@register.filter
def feature_label(feature):
    """Short display name for an audio feature."""
    return FEATURE_DISPLAY.get(feature, feature)


@register.filter
def feature_value(track, feature):
    """Format a track's audio feature value for display."""
    val = getattr(track, feature, None)
    if val is None:
        return "-"
    if feature == "loudness":
        return f"{val:.1f} dB"
    if feature == "tempo":
        return f"{val:.0f}"
    if feature == "duration_ms":
        s = val // 1000
        m, s = divmod(s, 60)
        return f"{m}:{s:02d}"
    # 0-1 features: show as percentage
    return f"{val:.0%}"


@register.filter
def get_item(dictionary, key):
    """Look up a key in a dict from a template."""
    return dictionary.get(key, "")


@register.filter
def sort_arrow(order):
    """Return an arrow character for the current sort direction."""
    return mark_safe("&#9650;") if order == "asc" else mark_safe("&#9660;")
