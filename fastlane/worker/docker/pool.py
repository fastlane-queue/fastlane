
# Standard Library
import random
import traceback

# 3rd Party
import docker
import pybreaker
import requests
from flask import current_app

# Fastlane
from fastlane.worker.errors import NoAvailableHostsError


class DockerPool:
    def __init__(self, docker_hosts):
        self.docker_hosts = docker_hosts

        self.max_running = {}
        self.clients_per_regex = []
        self.clients = {}
        self.__init_clients()

    def __init_clients(self):
        for regex, docker_hosts, max_running in self.docker_hosts:
            client_list = []
            clients = (regex, client_list)
            self.clients_per_regex.append(clients)
            self.max_running[regex] = max_running

            for address in docker_hosts:
                host, port = address.split(":")
                docker_client = docker.DockerClient(base_url=address)
                self.clients[address] = (host, int(port), docker_client)
                client_list.append((host, int(port), docker_client))

    @staticmethod
    def refresh_circuits(executor, clients, blacklisted_hosts, logger):
        def docker_ps(client):
            client.containers.list(sparse=False)

        for host, port, client in clients:
            if f"{host}:{port}" in blacklisted_hosts:
                continue

            try:
                logger.debug("Refreshing host...", host=host, port=port)
                circuit = executor.get_circuit(f"{host}:{port}")
                circuit.call(docker_ps, client)
            except (requests.exceptions.ConnectionError, pybreaker.CircuitBreakerError):
                error = traceback.format_exc()
                logger.error("Failed to refresh host.", error=error)

    def get_client(self, executor, task_id, host=None, port=None, blacklist=None):
        logger = current_app.logger.bind(
            task_id=task_id, host=host, port=port, blacklist=blacklist
        )

        if host is not None and port is not None:
            logger.debug("Custom host returned.")

            docker_client = self.clients.get(f"{host}:{port}")

            if docker_client is None:
                return host, port, None

            return docker_client

        if blacklist is None:
            blacklist = set()

        for regex, clients in self.clients_per_regex:
            logger.debug("Trying to retrieve docker client...", regex=regex)

            if regex is not None and not regex.match(task_id):
                logger.debug("Task ID does not match regex.", regex=regex)

                continue

            DockerPool.refresh_circuits(executor, clients, blacklist, logger)
            filtered = [
                (host, port, client)

                for (host, port, client) in clients

                if f"{host}:{port}" not in blacklist
                and executor.get_circuit(f"{host}:{port}").current_state == "closed"
            ]

            if not filtered:
                logger.debug(
                    "No non-blacklisted and closed circuit clients found for farm.",
                    regex=regex,
                )

                continue

            logger.info(
                "Returning random choice out of the remaining clients.",
                clients=[f"{host}:{port}" for (host, port, client) in filtered],
            )

            host, port, client = random.choice(filtered)

            return host, int(port), client

        msg = f"Failed to find a docker host for task id {task_id}."
        logger.error(msg)
        raise NoAvailableHostsError(msg)
