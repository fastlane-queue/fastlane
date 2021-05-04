from . import worker
from newlane.core.queue import queue


def enqueue_exec(exec_id: str, *args: tuple):
    return queue.enqueue(worker.run_container, exec_id, *args)

