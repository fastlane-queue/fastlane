import re
from datetime import timedelta

regex = re.compile(
    r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')


def parse_time(time_str):
    if time_str is None:
        return None

    parts = regex.match(time_str)

    if not parts:
        return None

    parts = parts.groupdict()
    time_params = {}

    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)

    return timedelta(**time_params)
