# 3rd Party
from flask import Blueprint, current_app
from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
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
            "fastlane_req_count",
            "Number of requests to Fastlane API",
            ["method", "endpoint", "status_code"],
            registry=registry,
        )

        self.request_duration = Summary(
            "fastlane_req_duration_ms",
            "Duration of all requests to Fastlane API",
            ["method", "endpoint", "status_code"],
            registry=registry,
        )

        self.request_duration_hist = Histogram(
            "fastlane_req_duration_histogram",
            "Histogram of the duration of all requests to Fastlane API",
            ["method", "endpoint", "status_code"],
            registry=registry,
        )

        self.image_download_count = Counter(
            "fastlane_image_download_count",
            "Number of all docker image downloads",
            ["task_id", "job_id", "execution_id", "image", "tag", "docker_host"],
            registry=registry,
        )

        self.image_download_duration = Summary(
            "fastlane_image_download_ms",
            "Duration of all docker image downloads",
            ["task_id", "job_id", "execution_id", "image", "tag", "docker_host"],
            registry=registry,
        )

        self.image_download_current = Gauge(
            "fastlane_image_downloads_current",
            "Current image downloads",
            ["task_id", "job_id", "execution_id", "image", "tag"],
            registry=self.registry,
        )

        self.docker_run_count = Counter(
            "fastlane_docker_run_count",
            "Number of all docker API run commands",
            ["task_id", "job_id", "execution_id", "docker_host"],
            registry=registry,
        )

        self.docker_run_duration = Summary(
            "fastlane_docker_run_ms",
            "Duration of all docker API run commands",
            ["task_id", "job_id", "execution_id", "docker_host"],
            registry=registry,
        )

        self.docker_run_current = Gauge(
            "fastlane_docker_run_current",
            "Current docker run commands being run in the API",
            ["task_id", "job_id", "execution_id", "docker_host"],
            registry=self.registry,
        )

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

    def report_image_download_start(self, job, execution, image, tag):
        self.image_download_current.labels(
            job.task.task_id, str(job.job_id), execution.execution_id, image, tag
        ).inc()
        self.submit(job="worker")

    def report_image_download_end(self, job, execution, image, tag):
        self.image_download_current.labels(
            job.task.task_id, str(job.job_id), execution.execution_id, image, tag
        ).dec()
        self.submit(job="worker")

    def report_image_download(self, job, execution, image, tag, docker_host, ellapsed):
        if not tag:
            tag = "latest"

        self.image_download_count.labels(
            job.task.task_id,
            str(job.job_id),
            execution.execution_id,
            image,
            tag,
            docker_host,
        ).inc()

        self.image_download_duration.labels(
            job.task.task_id,
            str(job.job_id),
            execution.execution_id,
            image,
            tag,
            docker_host,
        ).observe(ellapsed)

        self.submit(job="worker")

    def report_job_run_start(self, job, execution, docker_host):
        self.docker_run_current.labels(
            job.task.task_id, str(job.job_id), execution.execution_id, docker_host
        ).inc()
        self.submit(job="worker")

    def report_job_run_end(self, job, execution, docker_host):
        self.docker_run_current.labels(
            job.task.task_id, str(job.job_id), execution.execution_id, docker_host
        ).dec()
        self.submit(job="worker")

    def report_job_run(self, job, execution, docker_host, ellapsed):
        self.docker_run_count.labels(
            job.task.task_id, str(job.job_id), execution.execution_id, docker_host
        ).inc()

        self.docker_run_duration.labels(
            job.task.task_id, str(job.job_id), execution.execution_id, docker_host
        ).observe(ellapsed)

        self.submit(job="worker")

    def report_container_metrics(  # pylint: disable=too-many-arguments
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
        if rss is not None:
            metric = Gauge(
                "fastlane_container_memory_rss",
                "Container stats - memory rss",
                ["task_id", "job_id", "execution_id", "docker_host", "container_id"],
                registry=self.registry,
            )
            metric.labels(
                job.task.task_id,
                str(job.job_id),
                execution.execution_id,
                docker_host,
                container_id,
            ).set(rss)

        if total_rss is not None:
            metric = Gauge(
                "fastlane_container_memory_total_rss",
                "Container stats - memory total rss",
                ["task_id", "job_id", "execution_id", "docker_host", "container_id"],
                registry=self.registry,
            )
            metric.labels(
                job.task.task_id,
                str(job.job_id),
                execution.execution_id,
                docker_host,
                container_id,
            ).set(total_rss)

        if system_cpu_usage is not None:
            metric = Gauge(
                "fastlane_container_system_cpu_usage",
                "Container stats - system cpu usage",
                ["task_id", "job_id", "execution_id", "docker_host", "container_id"],
                registry=self.registry,
            )
            metric.labels(
                job.task.task_id,
                str(job.job_id),
                execution.execution_id,
                docker_host,
                container_id,
            ).set(system_cpu_usage)

        if total_cpu_usage is not None:
            metric = Gauge(
                "fastlane_container_total_cpu_usage",
                "Container stats - total cpu usage",
                ["task_id", "job_id", "execution_id", "docker_host", "container_id"],
                registry=self.registry,
            )
            metric.labels(
                job.task.task_id,
                str(job.job_id),
                execution.execution_id,
                docker_host,
                container_id,
            ).set(total_cpu_usage)

        if per_cpu_usage is not None:
            for index, cpu_usage in enumerate(per_cpu_usage):
                metric = Gauge(
                    f"fastlane_container_per_cpu_usage_{index}",
                    "Container stats - cpu usage per cpu index",
                    [
                        "task_id",
                        "job_id",
                        "execution_id",
                        "docker_host",
                        "container_id",
                    ],
                    registry=self.registry,
                )
                metric.labels(
                    job.task.task_id,
                    str(job.job_id),
                    execution.execution_id,
                    docker_host,
                    container_id,
                ).set(cpu_usage)

        self.submit(job="worker")

    def report_container_result(
        self, job, execution, docker_host, container_id, status, ellapsed
    ):
        container_duration = Summary(
            "fastlane_container_duration_ms",
            "Duration of container execution",
            [
                "task_id",
                "job_id",
                "execution_id",
                "docker_host",
                "container_id",
                "status",
            ],
            registry=self.registry,
        )
        container_duration.labels(
            job.task.task_id,
            str(job.job_id),
            execution.execution_id,
            docker_host,
            container_id,
            status,
        ).observe(ellapsed)

        container_duration_hist = Histogram(
            "fastlane_container_duration_histogram",
            "Histogram of duration of container execution",
            [
                "task_id",
                "job_id",
                "execution_id",
                "docker_host",
                "container_id",
                "status",
            ],
            registry=self.registry,
        )
        container_duration_hist.labels(
            job.task.task_id,
            str(job.job_id),
            execution.execution_id,
            docker_host,
            container_id,
            status,
        ).observe(ellapsed)

        self.submit(job="worker")
