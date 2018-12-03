import sys
from os.path import abspath, dirname, join

import click

from fastlane.cli.api import APIHandler
from fastlane.cli.worker import WorkerHandler

ROOT_CONFIG = abspath(join(dirname(__file__), '../config/local.conf'))

LEVELS = {
    0: 'ERROR',
    1: 'WARN',
    2: 'INFO',
    3: 'DEBUG',
}


@click.group()
def main():
    pass


@click.command()
@click.option('-b', '--host', default='0.0.0.0')
@click.option('-p', '--port', default=10000)
@click.option('-v', '--verbose', default=0, count=True)
@click.option(
    '-c',
    '--config',
    default=ROOT_CONFIG,
    help='configuration file to use with fastlane')
def api(host, port, verbose, config):
    """Runs fastlane API in the specified host and port."""

    log_level = LEVELS.get(verbose, 'ERROR')
    handler = APIHandler(click, host, port, config, log_level)
    handler()


@click.command()
@click.option('-i', '--id', default=None, help='ID for this worker')
@click.option(
    '-j',
    '--no-jobs',
    default=False,
    help='''Process the 'jobs' queue?''',
    is_flag=True)
@click.option(
    '-m',
    '--no-monitor',
    default=False,
    help='''Process the 'monitor' queue?''',
    is_flag=True)
@click.option('-v', '--verbose', default=0, count=True)
@click.option(
    '-c',
    '--config',
    default=ROOT_CONFIG,
    help='configuration file to use with fastlane')
def worker(id, no_jobs, no_monitor, verbose, config):
    """Runs an fastlane Worker with the specified queue name and starts processing."""
    jobs = not no_jobs
    monitor = not no_monitor

    if not jobs and not monitor:
        click.echo('Worker must monitor at least one queue: jobs or monitor')
        sys.exit(1)

    log_level = LEVELS.get(verbose, 'ERROR')
    handler = WorkerHandler(click, id, jobs, monitor, config, log_level)
    handler()


main.add_command(api)
main.add_command(worker)
