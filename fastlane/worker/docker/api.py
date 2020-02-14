# Standard Library
from json import loads

# 3rd Party
from flask import Blueprint, current_app, g, make_response, request
from validators import domain as validate_domain

bp = Blueprint(  # pylint: disable=invalid-name
    "docker", __name__, url_prefix="/docker-executor"
)

BLACKLIST_KEY = "docker-executor::blacklisted-hosts"


@bp.route("/blacklist", methods=["POST", "PUT"])
def add_to_blacklist():
    redis = current_app.redis

    data = get_details()

    if data is None or data == "":
        msg = "Failed to add host to blacklist because JSON body could not be parsed."
        g.logger.warn(msg)

        return make_response(msg, 400)

    if "host" not in data:
        msg = "Failed to add host to blacklist because 'host' attribute was not found in JSON body."
        g.logger.warn(msg)

        return make_response(msg, 400)

    host = data["host"]

    if not validate_hostname(host):
        msg = (
            "Failed to add host to blacklist because 'host'"
            " attribute had an invalid value."
        )
        g.logger.warn(msg)

        return make_response(msg, 400)

    redis.sadd(BLACKLIST_KEY, host)

    return ""


@bp.route("/blacklist", methods=["DEL", "DELETE"])
def remove_from_blacklist():
    redis = current_app.redis

    data = get_details()

    if data is None or data == "":
        msg = "Failed to remove host from blacklist because JSON body could not be parsed."
        g.logger.warn(msg)

        return make_response(msg, 400)

    if "host" not in data:
        msg = (
            "Failed to remove host from blacklist because 'host'"
            " attribute was not found in JSON body."
        )
        g.logger.warn(msg)

        return make_response(msg, 400)

    host = data["host"]

    if not validate_hostname(host):
        msg = (
            "Failed to remove host to blacklist because 'host'"
            " attribute had an invalid value."
        )
        g.logger.warn(msg)

        return make_response(msg, 400)

    redis.srem(BLACKLIST_KEY, host)

    return ""


def get_details():
    details = request.get_json()

    if details is None and request.get_data():
        details = loads(request.get_data())

    return details


def validate_hostname(value):
    values = value.split(':')

    if len(values) != 2:
        return False

    return validate_domain(values[0]) and values[1].isdigit()
