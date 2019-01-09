# Standard Library
import re
from unittest.mock import MagicMock, PropertyMock
from uuid import uuid4


class ContainerFixture:
    @staticmethod
    def get_logs(container_mock):
        def get(stdout=False, stderr=False):
            logs = []

            if stdout and isinstance(container_mock.stdout, (str, bytes)):
                logs.append(container_mock.stdout)

            if stderr and isinstance(container_mock.stderr, (str, bytes)):
                logs.append(container_mock.stderr)

            return "\n".join(logs)

        return get

    @staticmethod
    def new(
        name, container_id=None, state=None, status="created", stdout=None, stderr=None
    ):
        if container_id is None:
            container_id = f"fastlane-job-{str(uuid4())}"

        container_mock = MagicMock(attrs={}, status=status, id=container_id)
        name = PropertyMock(return_value=name)
        type(container_mock).name = name

        if state is not None:
            container_mock.attrs["State"] = state

        container_mock.logs.side_effect = ContainerFixture.get_logs(container_mock)
        container_mock.stdout = stdout
        container_mock.stderr = stderr

        return container_mock

    @staticmethod
    def new_with_status(
        name,
        status="created",
        paused=False,
        restarting=False,
        oom_killed=False,
        dead=False,
        pid=0,
        exit_code=None,
        custom_error=None,
        started_at=None,
        finished_at=None,
        stdout=None,
        stderr=None,
    ):
        return ContainerFixture.new(
            name,
            state={
                "Status": status,
                "Running": status == "running",
                "Paused": paused,
                "Restarting": restarting,
                "OOMKilled": oom_killed,
                "Dead": dead,
                "Pid": pid,
                "ExitCode": exit_code,
                "Error": custom_error,
                "StartedAt": started_at,
                "FinishedAt": finished_at,
            },
            status=status,
            stdout=stdout,
            stderr=stderr,
        )


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

        pool = MagicMock(
            clients=clients,
            clients_per_regex=clients_per_regex,
            max_running=max_running,
        )

        return pool

    @staticmethod
    def new_defaults(regex, host="host", port=1234, max_running=3, containers=None):
        if containers is None:
            containers = []

        match = re.compile(regex)
        client_mock = ClientFixture.new(containers)

        pool_mock = PoolFixture.new(
            clients={match: (host, port, client_mock)},
            clients_per_regex=[(match, [(host, port, client_mock)])],
            max_running={match: max_running},
        )
        pool_mock.get_client.return_value = (host, port, client_mock)

        return match, pool_mock, client_mock
