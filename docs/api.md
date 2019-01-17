# API/Workers

## API - Get all tasks

### Request Details

`Method`: `GET`

`URL`: `/tasks`

`Body`: -

`Query Parameters`:

* `page`: current page in the tasks pagination. Defaults to `1`.

### Example Response

```json
{
  "hasNext": false, 
  "hasPrev": false, 
  "items": [
    {
      "createdAt": 1547737982.644, 
      "jobsCount": 2, 
      "lastModifiedAt": 1547738263.561, 
      "taskId": "test-wrkng", 
      "url": "http://localhost:10000/tasks/test-wrkng"
    }
  ], 
  "nextUrl": null, 
  "page": 1, 
  "pages": 1, 
  "perPage": 10, 
  "prevUrl": null, 
  "total": 1
}
```

### Description

This route returns all the registered tasks in [fastlane](https://github.com/heynemann/fastlane).

Using the included details for pagination is advised. The `hasNext` and `hasPrev` flags can be used to determine the available directions for pagination. The `nextUrl` and `prevUrl` keys can be used to navigate in that direction. The number of pages can be determined by the `pages` key. The number of items per page can be obtained using the `perPage` key.

## API - Enqueue Job

### Request Details

`Method`: `POST`

`Url`: `/tasks/<task-id>`

`task-id` should be an arbitrary unique name that groups all jobs subsequently added to this same task.

`Body`:

```json
{
  "image": "ubuntu:latest",
  "command": "ls -lah",
  "envs": {
    "SMTP_SERVER":"my-smtp-server"
  },
  "metadata": {
    "username": "heynemann"
  },
  "retries": 3
}
```

For more options to the payload used in this route, please refer to the [Job Payload](job-payload.md) page.

`Query Parameters`: -

### Example Response

```json
{
  "jobId": "5a023792-1445-44e9-8a8b-cfe5ad05d1c6",
  "jobUrl": "http://localhost:10000/tasks/test-wrkng/jobs/5a023792-1445-44e9-8a8b-cfe5ad05d1c6",
  "queueJobId": "f1b526fa-acbf-4bb0-bd39-67621dee540a",
  "taskId": "test-wrkng",
  "taskUrl": "http://localhost:10000/tasks/test-wrkng"
}
```

### Description

`POST`ing to this route creates a new job and schedules it for execution.

If the database contains a task with the provided `task_id`, it will be used. Otherwise, a new task with the provided `task_id` will be created.

The response includes `IDs` that can be used to track the Job execution, as well as the task and job URLs to get further details.

The `queueJobId` key is the ID in the [RQ](http://python-rq.org/) queue and should not be very relevant for users of [fastlane](https://github.com/heynemann/fastlane).


## API - Enqueue/Update Job

### Request Details

`Method`: `PUT`

`Url`: `/tasks/<task-id>/jobs/<job-id>`

`task-id` should be an arbitrary unique name that groups all jobs subsequently added to this same task.
`job-id` should be a valid UUID4.

`Body`:

```json
{
  "image": "ubuntu:latest",
  "command": "ls -lah",
  "envs": {
    "SMTP_SERVER":"my-smtp-server"
  },
  "metadata": {
    "username": "heynemann"
  },
  "retries": 3
}
```

For more options to the payload used in this route, please refer to the [Job Payload](job-payload.md) page.

`Query Parameters`: -

### Example Response

```json
{
  "jobId": "5a023792-1445-44e9-8a8b-cfe5ad05d1c6",
  "jobUrl": "http://localhost:10000/tasks/test-wrkng/jobs/5a023792-1445-44e9-8a8b-cfe5ad05d1c6",
  "queueJobId": "f1b526fa-acbf-4bb0-bd39-67621dee540a",
  "taskId": "test-wrkng",
  "taskUrl": "http://localhost:10000/tasks/test-wrkng"
}
```

### Description

`PUT`ting to this route creates or updates job and schedules it for execution. The jobs is created if the supplied `job_id` does not exist in the task already. If it does, the existing job is updated with all the provided details and future executions will use the updated details.

All the the other details from the [enqueue route](#api-enqueue-job) also apply.

## API - Task Details

TBW.

## API - Job Details

TBW.

## API - Job stdout

TBW.

## API - Job stderr

TBW.

## API - Stop Job

TBW.

## API - Retry Job

TBW.

## API - Stream Job Logs

TBW.

## API - Websocket for Job Logs

TBW.

## API - Job Execution Details

TBW.

## API - Job Execution stdout

TBW.

## API - Job Execution stderr

TBW.

## API - Stop Job Execution Details

TBW.

## API - Stream Job Execution Logs

TBW.

## API - Websocket for Job Execution Logs

TBW.

## API - Healthcheck

TBW.

## API - Farm Status

TBW.

## Workers

TBW.
