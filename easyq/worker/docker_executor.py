import random

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

        self.clients = {}
        self.__init_clients()

    def __init_clients(self):
        for host, port in self.docker_hosts:
            cl = docker.DockerClient(base_url=f"{host}:{port}")
            self.clients[f"{host}:{port}"] = (host, port, cl)

    def get_client(self, host=None, port=None):
        if host is None and port is None:
            item = random.randint(0, len(self.clients) - 1)

            return tuple(self.clients.values())[item]

        return self.clients.get(f"{host}:{port}")


class Executor:
    def __init__(self, app, pool=None):
        self.app = app
        self.pool = pool

        if pool is None:
            self.pool = DockerPool(self.app.config["DOCKER_HOSTS"])

    def update_image(self, task, job, execution, image, tag):
        host, port, cl = self.pool.get_client()
        cl.images.pull(image, tag=tag)
        execution.metadata["docker_host"] = host
        execution.metadata["docker_port"] = port

    def run(self, task, job, execution, image, tag, command):
        h = execution.metadata["docker_host"]
        p = execution.metadata["docker_port"]
        host, port, cl = self.pool.get_client(h, p)

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
        host, port, cl = self.pool.get_client(h, p)

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

        return running
