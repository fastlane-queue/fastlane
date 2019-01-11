# Standard Library
import gzip
from io import BytesIO as IO

# 3rd Party
from flask import Blueprint, request

bp = Blueprint("gzip", __name__)  # pylint: disable=invalid-name


def init_app(app):
    def gzip_response(response):
        if response.headers["Content-Type"] != "application/json":
            return response

        accept_encoding = request.headers.get("Accept-Encoding", "")

        if "gzip" not in accept_encoding.lower():
            return response

        response.direct_passthrough = False

        if (
            response.status_code < 200
            or response.status_code >= 300
            or "Content-Encoding" in response.headers
        ):
            return response

        gzip_buffer = IO()
        gzip_file = gzip.GzipFile(mode="wb", fileobj=gzip_buffer)
        gzip_file.write(response.data)
        gzip_file.close()

        response.data = gzip_buffer.getvalue()
        response.headers["Content-Encoding"] = "gzip"
        response.headers["Vary"] = "Accept-Encoding"
        response.headers["Content-Length"] = len(response.data)

        return response

    app.after_request(gzip_response)
