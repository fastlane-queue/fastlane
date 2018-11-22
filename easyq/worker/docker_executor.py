import random
import re
from json import loads

import docker
from dateutil.parser import parse

from easyq.worker import ExecutionResult

# https://docs.docker.com/engine/reference/commandline/ps/#examples
# One of created, restarting, running, removing, paused, exited, or dead
STATUS = {
    "created": ExecutionResult.Status.created,
    "exited": ExecutionResult.Status.done,
    "dead": ExecutionResult.Status.failed,
    "running": ExecutionResult.Status.running,
}


class DockerPool:
    def __init__(self, docker_hosts):
        self.docker_hosts = docker_hosts

        self.clients_per_regex = []
        self.clients = {}
        self.__init_clients()

    def __init_clients(self):
        for regex, docker_hosts in self.docker_hosts:
            clients = (regex, [])
            self.clients_per_regex.append(clients)

            for address in docker_hosts:
                host, port = address.split(":")
                cl = docker.DockerClient(base_url=address)
                self.clients[address] = (host, port, cl)
                clients[1].append((host, port, cl))

    def get_client(self, task_id, host=None, port=None):
        if host is not None or port is not None:
            return self.clients.get(f"{host}:{port}")

        for regex, clients in self.clients_per_regex:
            if regex is not None and not regex.match(task_id):
                continue

            return random.choice(clients)

        raise RuntimeError(f"Failed to find a docker host for task id {task_id}.")


class Executor:
    def __init__(self, app, pool=None):
        self.app = app
        self.pool = pool

        if pool is None:
            docker_hosts = []
            clusters = loads(self.app.config["DOCKER_HOSTS"])

            for cluster in clusters:
                regex = cluster["match"]

                if not regex:
                    regex = None
                else:
                    regex = re.compile(regex)

                hosts = cluster["hosts"]
                docker_hosts.append((regex, hosts))

            self.pool = DockerPool(docker_hosts)

    def update_image(self, task, job, execution, image, tag):
        host, port, cl = self.pool.get_client(task.task_id)
        cl.images.pull(image, tag=tag)
        execution.metadata["docker_host"] = host
        execution.metadata["docker_port"] = port

    def run(self, task, job, execution, image, tag, command):
        h = execution.metadata["docker_host"]
        p = execution.metadata["docker_port"]
        host, port, cl = self.pool.get_client(task.task_id, h, p)

        container = cl.containers.run(
            image=f"{image}:{tag}",
            name=f"easyq_worker_{execution.execution_id}",
            command=command,
            detach=True,
            environment=job.metadata.get("envs", {}),
        )

        execution.metadata["container_id"] = container.id

        return True

    def convert_date(self, dt):
        return parse(dt)

    def get_result(self, task, job, execution):
        h = execution.metadata["docker_host"]
        p = execution.metadata["docker_port"]
        host, port, cl = self.pool.get_client(task.task_id, h, p)

        container_id = execution.metadata["container_id"]
        container = cl.containers.get(container_id)

        # container.attrs['State']
        # {'Status': 'exited', 'Running': False, 'Paused': False, 'Restarting': False,
        # 'OOMKilled': False, 'Dead': False, 'Pid': 0, 'ExitCode': 0, 'Error': '',
        # 'StartedAt': '2018-08-27T17:14:14.1951232Z', 'FinishedAt': '2018-08-27T17:14:14.2707026Z'}

        result = ExecutionResult(
            STATUS.get(container.status, ExecutionResult.Status.done)
        )

        state = container.attrs["State"]
        result.exit_code = state["ExitCode"]
        result.error = state["Error"]
        result.started_at = self.convert_date(state["StartedAt"])

        if (
            result.status == ExecutionResult.Status.done
            or result.status == ExecutionResult.Status.failed
        ):
            result.finished_at = self.convert_date(state["FinishedAt"])
            result.log = container.logs(stdout=True, stderr=False)

            if result.error != "":
                result.error += (
                    f"\n\nstderr:\n{container.logs(stdout=False, stderr=True)}"
                )
            else:
                result.error = container.logs(stdout=False, stderr=True)

        return result

    def get_running_containers(self):
        running = []

        for (host, port, client) in self.pool.clients.values():
            containers = client.containers.list(
                sparse=False, filters={"status": "running"}
            )

            for container in containers:
                if not container.name.startswith("easyq_worker_"):
                    continue
                running.append((host, port, container.id))

        return {
            "available": [
                f"{host}:{port}" for (host, port, client) in self.pool.clients.values()
            ],
            "running": running,
        }
