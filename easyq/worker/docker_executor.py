import docker
from dateutil.parser import parse

from easyq.worker import ExecutionResult

# https://docs.docker.com/engine/reference/commandline/ps/#examples
# One of created, restarting, running, removing, paused, exited, or dead
STATUS = {
    'created': ExecutionResult.Status.created,
    'exited': ExecutionResult.Status.done,
    'dead': ExecutionResult.Status.failed,
    'running': ExecutionResult.Status.running,
}


class Executor:
    def __init__(self, app, client=None):
        self.app = app
        self.client = client

        if client is None:
            self.client = docker.from_env()

    def update_image(self, task, job, execution, image, tag):
        self.client.images.pull(image, tag=tag)

    def run(self, task, job, execution, image, tag, command):
        container = self.client.containers.run(
            image=f'{image}:{tag}', command=command, detach=True)

        execution.metadata['container_id'] = container.id

        return True

    def convert_date(self, dt):
        return parse(dt)

    def get_result(self, task, job, execution):
        container_id = execution.metadata['container_id']
        container = self.client.containers.get(container_id)

        # container.attrs['State']
        # {'Status': 'exited', 'Running': False, 'Paused': False, 'Restarting': False,
        # 'OOMKilled': False, 'Dead': False, 'Pid': 0, 'ExitCode': 0, 'Error': '',
        # 'StartedAt': '2018-08-27T17:14:14.1951232Z', 'FinishedAt': '2018-08-27T17:14:14.2707026Z'}

        result = ExecutionResult(
            STATUS.get(container.status, ExecutionResult.Status.done))

        state = container.attrs['State']
        result.exit_code = state['ExitCode']
        result.error = state['Error']
        result.started_at = self.convert_date(state['StartedAt'])

        if result.status == ExecutionResult.Status.done or result.status == ExecutionResult.Status.failed:
            result.finished_at = self.convert_date(state['FinishedAt'])
            result.log = container.logs(stdout=True, stderr=False)

            if result.error != '':
                result.error += f'\n\nstderr:\n{container.logs(stdout=False, stderr=True)}'
            else:
                result.error = container.logs(stdout=False, stderr=True)

        return result
