from .base import Base

from newlane.models import Task, Job, Execution

job = Base(Job)
task = Base(Task)
execution = Base(Execution)
