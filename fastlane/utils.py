# Standard Library
import calendar
import re
import copy
from datetime import datetime, timedelta

# 3rd Party
import croniter

REGEX = re.compile(r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?")

try:
    from ujson import loads, dumps # NOQA pylint: disable=unused-import
except ImportError:
    from json import loads, dumps  # NOQA pylint: disable=unused-import


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
def to_unix(date):
    """Converts a datetime object to unixtime"""

    return calendar.timegm(date.utctimetuple())


def unix_now():
    return to_unix(datetime.utcnow())


def get_next_cron_timestamp(cron):
    itr = croniter.croniter(cron, datetime.utcnow())
    next_dt = itr.get_next(datetime)

    return next_dt


def words_redacted(data, blacklist_fn, replacements="***"):
    new_data = copy.deepcopy(data)
    def redacted(data_redacted):
        for key, val in data_redacted.items():
            if blacklist_fn(key):
                data_redacted[key] = replacements
                continue

            if isinstance(val, dict):
                redacted(val)

        return data_redacted

    return redacted(new_data)
