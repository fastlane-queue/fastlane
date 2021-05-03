import docker

from newlane.settings import settings

client = docker.DockerClient(base_url=settings.docker)
