# 3rd Party
from flask import Blueprint, current_app
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Histogram,
    Summary,
    push_to_gateway,
)
from slugify import slugify

# Fastlane
from fastlane.api.metrics import BaseMetricsReporter

bp = Blueprint("prometheus", __name__)  # pylint: disable=invalid-name


def init_app(app):
    #  app.middlewares_to_register.append(("/metrics", make_wsgi_app()))
    registry = CollectorRegistry()
    app.register_metrics_reporter(Prometheus(registry))


class Prometheus(BaseMetricsReporter):
    def __init__(self, registry):
        super(Prometheus, self).__init__()
        self.registry = registry

        self.request_count = Counter(
            "fastlane_request_count",
            "Number of requests to Fastlane API",
            ["method", "endpoint", "status_code"],
            registry=registry,
        )

        self.request_duration = Summary(
            "fastlane_request_duration_milliseconds",
            "Duration of all requests to Fastlane API",
            ["method", "endpoint", "status_code"],
            registry=registry,
        )

        self.request_duration_hist = Histogram(
            "fastlane_request_duration_hist_milliseconds",
            "Histogram of the duration of all requests to Fastlane API",
            ["method", "endpoint", "status_code"],
            registry=registry,
        )

        self.image_download_count = Counter(
            "fastlane_docker_image_download_count",
            "Number of all docker image downloads",
            ["execution_id", "image", "tag"],
            registry=registry,
        )

        self.image_download_duration = Summary(
            "fastlane_docker_image_download_duration_milliseconds",
            "Duration of all docker image downloads",
            ["execution_id", "image", "tag"],
            registry=registry,
        )
        self.image_download_duration_per_image = {}

    def submit(self, job="api"):
        gateway = current_app.config["PROMETHEUS_PUSHGATEWAY_ADDR"]
        logger = current_app.logger.bind(operation="prometheus.submit", gateway=gateway)
        logger.debug("Logging to Prometheus Pushgateway...")
        push_to_gateway(gateway, job=job, registry=self.registry)
        logger.info("Prometheus Pushgateway log done successfully.")

    def report_request(self, method, url, status_code, ellapsed):
        url_key = slugify(url).replace("-", "_")

        self.request_count.labels(method, url_key, status_code).inc()

        self.request_duration.labels(method, url_key, status_code).observe(ellapsed)

        self.request_duration_hist.labels(method, url_key, status_code).observe(
            ellapsed
        )

        self.submit()

    def report_image_download(self, execution, image, tag, ellapsed):
        if not tag:
            tag = "latest"

        self.image_download_count.labels(execution.execution_id, image, tag).inc()

        self.image_download_duration.labels(execution.execution_id, image, tag).observe(
            ellapsed
        )

        self.submit(job="worker")

    def report_job_run(self, execution, ellapsed):
        pass
        #  self.job_run_duration.observe(ellapsed)
        #  execution_id = str(execution.execution_id)
        #  summ = self.job_run_duration_per_image.get(execution_id)

        #  if summ is None:
        #  summ = self.job_run_duration_per_image[execution_id] = Summary(
        #  f"fastlane_docker_job_run_duration_{execution_id}_milliseconds",
        #  f"Duration of running docker container for execution {execution_id}.",
        #  registry=self.registry,
        #  )
        #  summ.observe(ellapsed)

        #  self.submit(job="worker")
