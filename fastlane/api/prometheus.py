# 3rd Party
from flask import Blueprint
from prometheus_client import Counter, Histogram, Summary, make_wsgi_app
from slugify import slugify

# Fastlane
from fastlane.api.metrics import BaseMetricsReporter

bp = Blueprint("prometheus", __name__)  # pylint: disable=invalid-name


def init_app(app):
    app.middlewares_to_register.append(("/metrics", make_wsgi_app()))
    app.register_metrics_reporter(Prometheus())


class Prometheus(BaseMetricsReporter):
    def __init__(self):
        self.request_count = Counter(
            "fastlane_request_count", "Number of requests to Fastlane API"
        )
        self.request_count_per_url = {}

        self.request_duration = Summary(
            "fastlane_request_duration_milliseconds",
            "Duration of all requests to Fastlane API",
        )
        self.request_duration_per_url = {}

        self.request_duration_hist = Histogram(
            "fastlane_request_duration_hist_milliseconds",
            "Histogram of the duration of all requests to Fastlane API",
        )
        self.request_duration_hist_per_url = {}

    def report_request(self, url, status_code, ellapsed):
        url_key = slugify(url)

        self.request_count.inc()
        counter = self.request_count_per_url.get(url_key)

        if counter is None:
            counter = self.request_count_per_url[url_key] = Counter(
                f"fastlane_request_count_{url_key}",
                f"Number of requests to Fastlane API for {url}",
            )
        counter.inc()

        self.request_duration.observe(ellapsed)
        summ = self.request_duration_per_url.get(url_key)

        if summ is None:
            summ = self.request_duration_per_url[url_key] = Summary(
                f"fastlane_request_duration_{url_key}_milliseconds",
                f"Duration of requests to Fastlane API for {url}",
            )
        summ.observe(ellapsed)

        self.request_duration_hist.observe(ellapsed)
        hist = self.request_duration_hist_per_url.get(url_key)

        if hist is None:
            hist = self.request_duration_hist_per_url[url_key] = Histogram(
                f"fastlane_request_duration_hist_{url_key}_milliseconds",
                f"Duration of requests to Fastlane API for {url}",
            )
        hist.observe(ellapsed)
