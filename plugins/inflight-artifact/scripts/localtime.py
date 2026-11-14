"""Turn the UTC timestamps GitHub and taskwarrior report into the user's local calendar days."""
import datetime


def to_local(utc_iso):
    """'2026-11-14T03:10:00Z' or '20261114T031000Z' -> aware datetime in the local zone."""
    s = utc_iso.strip()
    if "-" not in s:
        s = datetime.datetime.strptime(s, "%Y%m%dT%H%M%SZ").strftime("%Y-%m-%dT%H:%M:%S+00:00")
    return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone()


def local_date(utc_iso):
    """'YYYY-MM-DD' of that instant on the local calendar."""
    return to_local(utc_iso).date().isoformat()


def local_ymd(utc_iso):
    """'YYYYMMDD' of that instant on the local calendar, or '' when there is no timestamp."""
    return to_local(utc_iso).strftime("%Y%m%d") if utc_iso else ""


def _stamp(day, at):
    dt = datetime.datetime.combine(day, at).astimezone()
    z = dt.strftime("%z")
    return f"{day.isoformat()}T{at.strftime('%H:%M:%S')}{z[:3]}:{z[3:]}"


def day_start(day):
    """GitHub search timestamp for local midnight starting `day`."""
    return _stamp(day, datetime.time(0, 0, 0))


def day_range(day):
    """GitHub search range covering all of `day` in the local zone."""
    return f"{day_start(day)}..{_stamp(day, datetime.time(23, 59, 59))}"
