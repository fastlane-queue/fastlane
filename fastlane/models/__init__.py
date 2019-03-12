"""   isort:skip_file """

# 3rd Party
from flask_mongoengine import MongoEngine

db = MongoEngine()  # isort:skip pylint: disable=invalid-name

from fastlane.models.task import Task  # NOQA pylint: disable=unused-import,wrong-import-position
from fastlane.models.job import Job  # NOQA pylint: disable=unused-import,wrong-import-position
from fastlane.models.job_execution import JobExecution # NOQA pylint: disable=unused-import,wrong-import-position
