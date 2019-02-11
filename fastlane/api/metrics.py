# Standard Library
from datetime import datetime
from uuid import uuid4

# 3rd Party
from flask import Blueprint, current_app, g, request

bp = Blueprint("metrics", __name__)  # pylint: disable=invalid-name


class BaseMetricsReporter:
    def report_request(self, method, url, status_code, ellapsed):
        pass

    def report_image_download_start(self, job, execution, image, tag):
        pass

    def report_image_download(self, job, execution, image, tag, docker_host, ellapsed):
        pass

    def report_image_download_end(self, job, execution, image, tag):
        pass

    def report_job_run_start(self, job, execution, docker_host):
        pass

    def report_job_run(self, job, execution, docker_host, ellapsed):
        pass

    def report_job_run_end(self, job, execution, docker_host):
        pass

    def report_container_metrics(
        self,
        job,
        execution,
        docker_host,
        container_id,
        rss,
        total_rss,
        total_cpu_usage,
        system_cpu_usage,
        per_cpu_usage,
    ):
        pass

    def report_container_result(
        self, job, execution, docker_host, container_id, status, ellapsed
    ):
        pass


def init_app(app):
    def start_timer():
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        g.logger = current_app.logger.bind(request_id=request_id)
        g.request_id = request_id
        g.start = datetime.now()

    app.before_request(start_timer)

    def log_request(response):
        if request.path == "/favicon.ico":
            return response

        now = datetime.now()
        duration = int(round((now - g.start).microseconds / 1000, 2))

        user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        host = request.host.split(":", 1)[0]

        log_params = {
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration": duration,
            "ip": user_ip,
            "host": host,
        }

        request_id = g.request_id

        if request_id:
            log_params["request_id"] = request_id

        current_app.report_metric(
            "report_request",
            request.method,
            request.path,
            response.status_code,
            duration,
        )

        if response.status_code < 400:
            current_app.logger.info("Request succeeded", **log_params)
        elif response.status_code < 500:
            current_app.logger.info("Bad Request", **log_params)
        else:
            current_app.logger.error("Internal Server Error", **log_params)

        return response

    app.after_request(log_request)
