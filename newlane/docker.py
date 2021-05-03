import docker

from newlane.settings import settings

client = docker.DockerClient(base_url=settings.docker)


def execute(image: str, command: str):
    client.containers.run(image=image, command=command)
    