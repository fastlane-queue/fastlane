import time

from flask import Blueprint, current_app, g, request

bp = Blueprint('metrics', __name__)


def init_app(app):
    @app.before_request
    def start_timer():
        g.start = time.time()

    @app.after_request
    def log_request(response):
        if request.path == '/favicon.ico':
            return response

        now = time.time()
        duration = round(now - g.start, 2)

        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        host = request.host.split(':', 1)[0]

        log_params = {
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': duration,
            'ip': ip,
            'host': host,
        }

        request_id = request.headers.get('X-Request-ID')

        if request_id:
            log_params['request_id'] = request_id

        if response.status_code < 400:
            current_app.logger.info('Request succeeded', **log_params)
        elif response.status_code < 500:
            current_app.logger.info('Bad Request', **log_params)
        else:
            current_app.logger.info('Internal Server Error', **log_params)

        return response
