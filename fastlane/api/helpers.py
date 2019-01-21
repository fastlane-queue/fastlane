# 3rd Party
from flask import current_app, make_response

# Fastlane
from fastlane.helpers import dumps


def return_error(msg, operation, status=500, logger=None):
    if logger is None:
        logger = current_app.bind(operation=operation)

    logger.error(msg)

    return make_response(dumps({"error": msg, "operation": operation}), status)
