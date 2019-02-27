# Standard Library
import calendar
import re
from datetime import datetime, timedelta

# 3rd Party
import croniter

REGEX = re.compile(r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?")

try:
    from ujson import loads, dumps
except ImportError:
    from json import loads, dumps  # NOQA


def parse_time(time_str):
    if time_str is None:
        return None

    parts = REGEX.match(time_str)

    if not parts:
        return None

    parts = parts.groupdict()
    time_params = {}

    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)

    return timedelta(**time_params)


# from_unix from times.from_unix()
def from_unix(string):
    """Convert a unix timestamp into a utc datetime"""

    return datetime.utcfromtimestamp(float(string))


# to_unix from times.to_unix()
def to_unix(dt):
    """Converts a datetime object to unixtime"""

    return calendar.timegm(dt.utctimetuple())


def get_next_cron_timestamp(cron):
    itr = croniter.croniter(cron, datetime.utcnow())
    next_dt = itr.get_next(datetime)

    return next_dt
