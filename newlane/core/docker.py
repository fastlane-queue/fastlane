import docker

from newlane.config import settings

docker = docker.DockerClient(base_url=settings.docker)
