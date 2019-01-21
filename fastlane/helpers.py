try:
    from ujson import loads, dumps  # pylint: disable=unused-import
except ImportError:
    from json import loads, dumps  # pylint: disable=unused-import
