# Standard Library
from unittest.mock import MagicMock, PropertyMock


class ContainerFixture:
    @staticmethod
    def new(name):
        container_mock = MagicMock()
        name = PropertyMock(return_value=name)
        type(container_mock).name = name

        return container_mock


class ClientFixture:
    @staticmethod
    def new(containers=None):
        if containers is None:
            containers = []

        client_mock = MagicMock()
        client_mock.containers.list.return_value = containers

        return client_mock


class PoolFixture:
    @staticmethod
    def new(clients=None, clients_per_regex=None, max_running=None):
        if clients is None:
            clients = {}

        if clients_per_regex is None:
            clients_per_regex = []

        if max_running is None:
            max_running = {}

        return MagicMock(
            clients=clients,
            clients_per_regex=clients_per_regex,
            max_running=max_running,
        )
