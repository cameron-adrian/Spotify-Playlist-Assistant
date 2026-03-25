from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def make_time_readable_hours(duration):
    if duration is None:
        return "N/A"

    minutes, seconds = divmod(duration, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours} hours, {minutes} minutes, {seconds} seconds"


@register.filter
def make_time_readable_minutes(duration):
    if duration is None:
        return "N/A"

    minutes, seconds = divmod(duration, 60)
    return f"{int(minutes)} minutes, {int(round(seconds,0))} seconds"


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
