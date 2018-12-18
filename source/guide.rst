.. _guide:

User Guide
==========

Running a new Job
-----------------

This Http POST will run an ubuntu container and then run the ls -lah command, as soon as there's a free working in fastlane.

.. code-block:: shell

    curl -X POST http://fastlane.local:10000/tasks/test-task \
        -d '{
                "image": "ubuntu:latest",
                "command": "ls -lah"
            }' 

The API response is the following:

.. code-block:: json

    {
        "taskId": "test-task",
        "jobId": "5c094abcedc7d5be820e20da",
        "queueJobId": "db72db9b-cb49-44bd-b2fa-b3afc8e3a041",
        "jobUrl": "http://fastlane.local:10000/tasks/test-task/jobs/5c094abcedc7d5be820e20da",
        "taskUrl": "http://fastlane.local:10000/tasks/test-task"
    }

In order to find more about the running (or done by now) job, just follow the jobUrl parameter of the returned JSON.

Running at a specific point in the future
---------------------------------------------------

This Http POST will run an ubuntu container and then run the ls -lah command, at Thursday, February 17, 2022 4:01:32 PM GMT.

.. code-block:: shell

    curl -X POST http://fastlane.local:10000/tasks/test-scheduled-task \
        -d '{
                "image": "ubuntu:latest",
                "command": "ls -lah",
                "startAt": 1645113692
            }' 

The API response is the following:

.. code-block:: json

    {
        "taskId": "test-scheduled-task",
        "jobId": "5c094abcedc7d5be820e20da",
        "queueJobId": "db72db9b-cb49-44bd-b2fa-b3afc8e3a041",
        "jobUrl": "http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da",
        "taskUrl": "http://fastlane.local:10000/tasks/test-scheduled-task"
    }

In order to find more about the running (or done by now) job, just follow the jobUrl parameter of the returned JSON.

Running in 5 minutes
--------------------

This Http POST will run an ubuntu container and then run the ls -lah command, in 5 minutes.

.. code-block:: shell

    curl -X POST http://fastlane.local:10000/tasks/test-scheduled-task \
        -d '{
                "image": "ubuntu:latest",
                "command": "ls -lah",
                "startIn": "5m"
            }' 

The API response is the following:

.. code-block:: json

    {
        "taskId": "test-scheduled-task",
        "jobId": "5c094abcedc7d5be820e20da",
        "queueJobId": "db72db9b-cb49-44bd-b2fa-b3afc8e3a041",
        "jobUrl": "http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da",
        "taskUrl": "http://fastlane.local:10000/tasks/test-scheduled-task"
    }

Supported formats also include: 10s, 2m30s, 4h30m25s, 2h30m, 240h.

In order to find more about the running (or done by now) job, just follow the jobUrl parameter of the returned JSON.

