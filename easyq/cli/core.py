import sys
from os.path import abspath, dirname, join

import click

from easyq.cli.api import APIHandler
from easyq.cli.worker import WorkerHandler

ROOT_CONFIG = abspath(join(dirname(__file__), '../config/local.conf'))


@click.group()
def main():
    pass


@click.command()
@click.option('-b', '--host', default='0.0.0.0')
@click.option('-p', '--port', default=10000)
@click.option(
    '-c',
    '--config',
    default=ROOT_CONFIG,
    help='configuration file to use with easyq')
def api(host, port, config):
    """Runs easyq API in the specified host and port."""
    handler = APIHandler(click, host, port, config)
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
@click.option(
    '-c',
    '--config',
    default=ROOT_CONFIG,
    help='configuration file to use with easyq')
def worker(id, no_jobs, no_monitor, config):
    """Runs an easyq Worker with the specified queue name and starts processing."""
    jobs = not no_jobs
    monitor = not no_monitor

    if not jobs and not monitor:
        click.echo('Worker must monitor at least one queue: jobs or monitor')
        sys.exit(1)

    handler = WorkerHandler(click, id, jobs, monitor, config)
    handler()


main.add_command(api)
main.add_command(worker)
