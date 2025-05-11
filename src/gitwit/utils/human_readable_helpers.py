from datetime import timedelta


def humanise_timedelta(delta: timedelta) -> str:
    if delta < timedelta(minutes=1):
        return f"{int(delta.total_seconds())} sec ago"
    if delta < timedelta(hours=1):
        return f"{int(delta.total_seconds()//60)} min ago"
    if delta < timedelta(days=1):
        return f"{delta.seconds//3600} hour(s) ago"

    return f"{delta.days} day(s) ago"
