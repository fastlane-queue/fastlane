from os.path import abspath, dirname, join

import click

from easyq.cli.api import APIHandler

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
    handler = APIHandler(click, host, port, config)
    handler()


main.add_command(api)
