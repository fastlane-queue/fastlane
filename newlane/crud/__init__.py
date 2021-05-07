from fastapi import HTTPException

from .crud import Crud
from newlane import models


task = Crud(models.Task)
job = Crud(models.Job, sort=models.Job.created_at.desc())
execution = Crud(models.Execution, sort=models.Execution.created_at.desc())
