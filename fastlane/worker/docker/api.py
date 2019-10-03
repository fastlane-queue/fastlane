# Standard Library
from json import loads

# 3rd Party
from flask import Blueprint, current_app, g, make_response, request

bp = Blueprint(  # pylint: disable=invalid-name
    "docker", __name__, url_prefix="/docker-executor"
)

BLACKLIST_KEY = "docker-executor::blacklisted-hosts"


def validate_host(host):
    """
    Validate if host follows desired standards. ('host:port')
    """
    host_for_validate = host.split(':')
    if len(host_for_validate) != 2:
        msg = "Failed to add host to blacklist, we did not identify the formed 'host: port'"
        g.logger.warn(msg)

        return make_response(msg, 400)
    else:
        try:
            int(host_for_validate[1])
        except ValueError:
            msg = "Failed to add host to blacklist, the port is not an integer."
            g.logger.warn(msg)

            return make_response(msg, 400)
    return True


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

    if validate_host(host):
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

    if validate_host(host):
        redis.srem(BLACKLIST_KEY, host)

    return ""


def get_details():
    details = request.get_json()

    if details is None and request.get_data():
        details = loads(request.get_data())

    return details
