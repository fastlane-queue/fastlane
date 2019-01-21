# Standard Library
import sys
from os.path import abspath, dirname, join

# 3rd Party
import click
import pkg_resources

# Fastlane
from fastlane.cli.api import APIHandler
from fastlane.cli.prune import PruneHandler
from fastlane.cli.worker import WorkerHandler

ROOT_CONFIG = abspath(join(dirname(__file__), "../config/local.conf"))

LEVELS = {0: "ERROR", 1: "WARN", 2: "INFO", 3: "DEBUG"}


@click.group()
def main():
    pass


@click.command()
def version():
    """Returns fastlane version."""

    click.echo(pkg_resources.get_distribution("fastlane").version)


@click.command()
@click.option("-b", "--host", default="0.0.0.0")
@click.option("-p", "--port", default=10000)
@click.option("-v", "--verbose", default=0, count=True)
@click.option(
    "-c",
    "--config-file",
    default=ROOT_CONFIG,
    help="configuration file to use with fastlane",
)
def api(host, port, verbose, config_file):
    """Runs fastlane API in the specified host and port."""

    log_level = LEVELS.get(verbose, "ERROR")
    handler = APIHandler(click, host, port, config_file, log_level)
    handler()


@click.command()
@click.option("-i", "--worker-id", default=None, help="ID for this worker")
@click.option(
    "-j", "--no-jobs", default=False, help="""Process the 'jobs' queue?""", is_flag=True
)
@click.option(
    "-m",
    "--no-monitor",
    default=False,
    help="""Process the 'monitor' queue?""",
    is_flag=True,
)
@click.option(
    "-n",
    "--no-notify",
    default=False,
    help="""Process the 'notify' queue?""",
    is_flag=True,
)
@click.option(
    "-w",
    "--no-webhooks",
    default=False,
    help="""Process the 'webhooks' queue?""",
    is_flag=True,
)
@click.option("-v", "--verbose", default=0, count=True)
@click.option(
    "-c",
    "--config-file",
    default=ROOT_CONFIG,
    help="configuration file to use with fastlane",
)
def worker(
    worker_id, no_jobs, no_monitor, no_notify, no_webhooks, verbose, config_file
):
    """Runs an fastlane Worker with the specified queue name and starts processing."""
    jobs = not no_jobs
    monitor = not no_monitor
    notify = not no_notify
    webhooks = not no_webhooks

    if not jobs and not monitor and not notify and not webhooks:
        click.echo(
            "Worker must monitor at least one queue: jobs, monitor, notify or webhooks"
        )
        sys.exit(1)

    log_level = LEVELS.get(verbose, "ERROR")
    handler = WorkerHandler(
        click, worker_id, jobs, monitor, notify, webhooks, config_file, log_level
    )
    handler()


@click.command()
def config():
    """Prints the default config for fastlane"""
    from fastlane.config import Config

    print(Config.get_config_text())


@click.command()
@click.option("-v", "--verbose", default=0, count=True)
@click.option(
    "-c",
    "--config-file",
    default=ROOT_CONFIG,
    help="configuration file to use with fastlane",
)
def prune(verbose, config_file):
    """Removes all containers that have already been processed by fastlane."""
    log_level = LEVELS.get(verbose, "ERROR")
    handler = PruneHandler(click, config_file, log_level)
    handler()


main.add_command(version)
main.add_command(api)
main.add_command(worker)
main.add_command(config)
main.add_command(prune)
