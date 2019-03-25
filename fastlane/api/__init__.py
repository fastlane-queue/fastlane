# Standard Library
from functools import wraps

# 3rd Party
from flask import g

# Fastlane
from fastlane.api.helpers import return_error
from fastlane.models import Job, Task


def load_parameters(config_parameters):
    def wrapper(func):
        @wraps(func)
        def params_func(*args, **kwargs):
            func_name = func.__name__
            if kwargs is not None:
                for conf in config_parameters:
                    key_in = conf["parameter_name_in"]
                    val_in = kwargs.get(key_in)

                    if val_in is not None:
                        params_method = {key_in: val_in}

                        if conf.get("deps"):
                            for dep in conf["deps"]:
                                kclass, field = dep.split(".")
                                params_method[field] = getattr(kwargs[kclass], field)

                        result_method = conf["parameter_method"](**params_method)

                        if result_method is None:
                            logger = g.logger.bind(operation=func_name, **params_method)
                            message_not_found_error = conf["message_not_found_error"].format(
                                **params_method
                            )
                            return return_error(
                                message_not_found_error, func_name, status=404, logger=logger
                            )

                        if conf["message_found_success"]:
                            logger = g.logger.bind(operation=func_name, **params_method)
                            logger.debug(conf["message_found_success"])

                        kwargs[conf["parameter_name_out"]] = result_method
                        del kwargs[key_in]

            return func(*args, **kwargs)

        return params_func

    return wrapper


CONF_TASK_ID = {
    "parameter_method": Task.get_by_task_id,
    "parameter_name_in": "task_id",
    "parameter_name_out": "task",
    "message_not_found_error": "Task ({task_id}) not found.",
    "message_found_success": "Task retrieved successfully...",
}

CONF_JOB_ID = {
    "parameter_method": Job.get_by_id,
    "parameter_name_in": "job_id",
    "parameter_name_out": "job",
    "message_not_found_error": "Job ({job_id}) with Task ({task_id}) not found.",
    "message_found_success": "Job retrieved successfully...",
    "deps": ["task.task_id"],
}

PARAMETER_TASK = [CONF_TASK_ID]

PARAMETER_TASK_JOB = [CONF_TASK_ID, CONF_JOB_ID]
