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
            registry=registry,
        )
        self.request_count_per_url = {}

        self.request_duration = Summary(
            "fastlane_request_duration_milliseconds",
            "Duration of all requests to Fastlane API",
            registry=registry,
        )
        self.request_duration_per_url = {}

        self.request_duration_hist = Histogram(
            "fastlane_request_duration_hist_milliseconds",
            "Histogram of the duration of all requests to Fastlane API",
            registry=registry,
        )
        self.request_duration_hist_per_url = {}

        self.image_download_count = Counter(
            "fastlane_docker_image_download_count",
            "Number of all docker image downloads",
            registry=registry,
        )
        self.image_download_count_per_image = {}

        self.image_download_duration = Summary(
            "fastlane_docker_image_download_duration_milliseconds",
            "Duration of all docker image downloads",
            registry=registry,
        )
        self.image_download_duration_per_image = {}

    def submit(self, job="api"):
        gateway = current_app.config["PROMETHEUS_PUSHGATEWAY_ADDR"]
        logger = current_app.logger.bind(operation="prometheus.submit", gateway=gateway)
        logger.debug("Logging to Prometheus Pushgateway...")
        push_to_gateway(gateway, job=job, registry=self.registry)
        logger.info("Prometheus Pushgateway log done successfully.")

    def report_request(self, url, status_code, ellapsed):
        url_key = slugify(url).replace("-", "_")

        self.request_count.inc()
        counter = self.request_count_per_url.get(url_key)

        if counter is None:
            counter = self.request_count_per_url[url_key] = Counter(
                f"fastlane_request_{url_key}_count",
                f"Number of requests to Fastlane API for {url}",
                registry=self.registry,
            )
        counter.inc()

        self.request_duration.observe(ellapsed)
        summ = self.request_duration_per_url.get(url_key)

        if summ is None:
            summ = self.request_duration_per_url[url_key] = Summary(
                f"fastlane_request_duration_{url_key}_milliseconds",
                f"Duration of requests to Fastlane API for {url}",
                registry=self.registry,
            )
        summ.observe(ellapsed)

        self.request_duration_hist.observe(ellapsed)
        hist = self.request_duration_hist_per_url.get(url_key)

        if hist is None:
            hist = self.request_duration_hist_per_url[url_key] = Histogram(
                f"fastlane_request_duration_hist_{url_key}_milliseconds",
                f"Duration of requests to Fastlane API for {url}",
                registry=self.registry,
            )
        hist.observe(ellapsed)

        self.submit()

    def report_image_download(self, image, tag, ellapsed):
        if not tag:
            tag = "latest"
        image_key = f"{image}_{tag}"

        self.image_download_count.inc()
        counter = self.image_download_count_per_image.get(image_key)

        if counter is None:
            counter = self.image_download_count_per_image[image_key] = Counter(
                f"fastlane_docker_image_download_{image_key}_count",
                f"Number of downloads of {image}:{tag}.",
                registry=self.registry,
            )
        counter.inc()

        self.image_download_duration.observe(ellapsed)
        summ = self.image_download_duration_per_image.get(image_key)

        if summ is None:
            summ = self.image_download_duration_per_image[image_key] = Summary(
                f"fastlane_docker_image_download_duration_{image_key}_milliseconds",
                f"Duration of download of docker image {image}:{tag}.",
                registry=self.registry,
            )
        summ.observe(ellapsed)

        self.submit(job="worker")
