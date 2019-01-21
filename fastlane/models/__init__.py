"""   isort:skip_file """

# 3rd Party
from flask_mongoengine import MongoEngine

db = MongoEngine()  # isort:skip pylint: disable=invalid-name

from fastlane.models.task import (  # NOQA pylint: disable=unused-import,wrong-import-position
    Task,
)
from fastlane.models.job import (  # NOQA pylint: disable=unused-import,wrong-import-position
    JobExecution,
    Job,
)
