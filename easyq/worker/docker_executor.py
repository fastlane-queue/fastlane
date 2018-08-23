import docker


class Executor:
    def __init__(self, app, client=None):
        self.app = app
        self.client = client

        if client is None:
            self.client = docker.from_env()

    def pull(self, image, tag):
        self.client.images.pull(image, tag=tag)

    def run(self, image, tag, command):
        container = self.client.containers.run(
            image=f'{image}:{tag}', command=command, detach=True)

        return container.id
