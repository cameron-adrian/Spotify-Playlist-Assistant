from django import template

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
