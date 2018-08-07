from os.path import join, abspath, dirname

import click

from easyq.cli.api import APIHandler

ROOT_CONFIG = abspath(join(dirname(__file__), '../config/local.conf'))


@click.group()
def main():
    pass


@click.command()
@click.option(
    '-c',
    '--config',
    default=ROOT_CONFIG,
    help='configuration file to use with easyq')
def api(config):
    handler = APIHandler(click, config)
    handler()


main.add_command(api)
