# API/Workers

## API - Enqueue Job

### Request Details

`Method`: `POST`

`URL`: `/tasks/<task-id>/`

* `task-id` should be an arbitrary unique name that groups all jobs subsequently added to this same task.

`Body`:

```json
{
  "image": "task1:latest",
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
  "executionId": "36e1b166-7c7a-4a41-a69e-8f78a9ec8128",
  "executionUrl": "http://localhost:10000/tasks/test-wrkng/jobs/5a023792-1445-44e9-8a8b-cfe5ad05d1c6/executions/36e1b166-7c7a-4a41-a69e-8f78a9ec8128/",
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

The response includes `IDs` that can be used to track the Taks, Job  and Job Execution, as well as the the respective URLs to get further details.

The `queueJobId` key is the ID in the [RQ](http://python-rq.org/) queue and should not be very relevant for users of [fastlane](https://github.com/heynemann/fastlane).

If the execution for the enqueued job is delayed (CRON or scheduled job), then the execution ID and URL will be null. The owner of the job must poll the job details URL later on to retrieve the execution id.

## API - Get all tasks

### Request Details

`Method`: `GET`

`URL`: `/tasks/`

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
      "createdAt": "2019-01-17T15:13:02.754000", 
      "jobsCount": 2, 
      "lastModifiedAt": "2019-01-17T15:13:02.754000", 
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

## API - Search tasks

### Request Details

`Method`: `GET`

`URL`: `/search/`

`Body`: -

`Query Parameters`:

* `query`: text to be searched in `task_id`.
* `page`: current page in the tasks pagination. Defaults to `1`.

### Example Response

```json
{
  "hasNext": false, 
  "hasPrev": false, 
  "items": [
    {
      "createdAt": "2019-01-17T15:13:02.754000", 
      "jobsCount": 2, 
      "lastModifiedAt": "2019-01-17T15:13:02.754000", 
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

This route searches for tasks by `task_id` in [fastlane](https://github.com/heynemann/fastlane).

The query is done by complete words, so if you search for `hel`, you won't find `hello`. On the other hand, you only need to know one complete word, so searching for `world` will find `hello-world`.

Using the included details for pagination is advised. The `hasNext` and `hasPrev` flags can be used to determine the available directions for pagination. The `nextUrl` and `prevUrl` keys can be used to navigate in that direction. The number of pages can be determined by the `pages` key. The number of items per page can be obtained using the `perPage` key.

## API - Enqueue/Update Job

### Request Details

`Method`: `PUT`

`URL`: `/tasks/<task-id>/jobs/<job-id>/`

* `task-id` should be an arbitrary unique name that groups all jobs subsequently added to this same task.
* `job-id` should be a valid UUID4.

`Body`:

```json
{
  "image": "task1:latest",
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

`PUT`ting to this route creates or updates job and schedules it for execution. The jobs is created if the supplied `job-id` does not exist in the task already. If it does, the existing job is updated with all the provided details and future executions will use the updated details.

All the the other details from the [enqueue route](#api-enqueue-job) also apply.

## API - Task Details

### Request Details

`Method`: `GET`

`URL`: `/tasks/<task-id>/`

* `task-id` is the ID for the desired task.

`Body`: -

`Query Parameters`: -

### Example Response

```json
{
  "jobs": [
    {
      "id": "2d3694e2-68eb-418f-82d5-605a801cbd8d", 
      "url": "http://localhost:10000/tasks/test-wrkng/jobs/2d3694e2-68eb-418f-82d5-605a801cbd8d"
    }, 
  ], 
  "taskId": "test-wrkng"
}
```

### Description

This route returns the jobs for this task.

## API - Job Details

### Request Details

`Method`: `GET`

`URL`: `/tasks/<task-id>/jobs/<job-id>/`

* `task-id` is the ID for the required task.
* `job-id` is the ID for the required job.

`Body`: -

`Query Parameters`:

* `page`: current page in the executions pagination. Defaults to `1`. The first page are the last 20 executions, page 2 starts in the 40th from the last execution and ends in the 21st execution from the last, and so on (TODO: Not implemented yet).

### Example Response

```json
{
  "job": {
    "createdAt": "2019-01-17T15:13:02.614000", 
    "executionCount": 1, 
    "executions": [
      {
        "command": "ls -lah", 
        "createdAt": "2019-01-17T15:13:02.754000", 
        "error": "", 
        "exitCode": 0, 
        "finishedAt": "2019-01-17T15:13:16.298000", 
        "image": "task1", 
        "log": "total 72K\ndrwxr-xr-x   1 root root 4.0K Jan 17 15:13 .\ndrwxr-xr-x   1 root root 4.0K Jan 17 15:13 ..\n-rwxr-xr-x   1 root root    0 Jan 17 15:13 .dockerenv\ndrwxr-xr-x   2 root root 4.0K Dec  4 17:12 bin\ndrwxr-xr-x   2 root root 4.0K Apr 24  2018 boot\ndrwxr-xr-x   5 root root  340 Jan 17 15:13 dev\ndrwxr-xr-x   1 root root 4.0K Jan 17 15:13 etc\ndrwxr-xr-x   2 root root 4.0K Apr 24  2018 home\ndrwxr-xr-x   8 root root 4.0K Dec  4 17:11 lib\ndrwxr-xr-x   2 root root 4.0K Dec  4 17:11 lib64\ndrwxr-xr-x   2 root root 4.0K Dec  4 17:11 media\ndrwxr-xr-x   2 root root 4.0K Dec  4 17:11 mnt\ndrwxr-xr-x   2 root root 4.0K Dec  4 17:11 opt\ndr-xr-xr-x 200 root root    0 Jan 17 15:13 proc\ndrwx------   2 root root 4.0K Dec  4 17:12 root\ndrwxr-xr-x   1 root root 4.0K Dec 28 23:22 run\ndrwxr-xr-x   1 root root 4.0K Dec 28 23:22 sbin\ndrwxr-xr-x   2 root root 4.0K Dec  4 17:11 srv\ndr-xr-xr-x  13 root root    0 Dec 20 12:50 sys\ndrwxrwxrwt   2 root root 4.0K Dec  4 17:12 tmp\ndrwxr-xr-x   1 root root 4.0K Dec  4 17:11 usr\ndrwxr-xr-x   1 root root 4.0K Dec  4 17:12 var\n", 
        "metadata": {
          "container_id": "cbab7fd2125a30acd91813dd5b91476ab2c8c1e93d84c1b791231097f16fc87c", 
          "docker_host": "localhost", 
          "docker_port": 1234
        }, 
        "startedAt": "2019-01-17T15:13:10.999000", 
        "status": "done"
      }
    ], 
    "lastModifiedAt": "2019-01-17T15:13:16.298000", 
    "metadata": {
      "enqueued_id": "ba17fb94-9d5b-463b-9e1e-0a572c8f8380", 
      "envs": {}, 
      "notify": {
        "fails": [], 
        "finishes": [], 
        "succeeds": []
      }, 
      "retries": 0, 
      "retry_count": 0, 
      "timeout": 1800, 
      "webhooks": {
        "fails": [], 
        "finishes": [], 
        "succeeds": []
      }
    }, 
    "scheduled": false, 
    "taskId": "test-wrkng"
  }, 
  "task": {
    "id": "test-wrkng", 
    "url": "http://localhost:10000/tasks/test-wrkng"
  }
}
```

### Description

This route returns the details for this job and all its last 20 executions, with their details.

## API - Job logs

### Request Details

`Method`: `GET`

`URL`: `/tasks/<task-id>/jobs/<job-id>/logs/`

* `task-id` is the ID for the required task.
* `job-id` is the ID for the required job.

`Body`: -

`Query Parameters`: -

### Example Response

```
total 72K
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 .
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 ..
-rwxr-xr-x   1 root root    0 Jan 17 15:13 .dockerenv
drwxr-xr-x   2 root root 4.0K Dec  4 17:12 bin
drwxr-xr-x   2 root root 4.0K Apr 24  2018 boot
drwxr-xr-x   5 root root  340 Jan 17 15:13 dev
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 etc
drwxr-xr-x   2 root root 4.0K Apr 24  2018 home
drwxr-xr-x   8 root root 4.0K Dec  4 17:11 lib
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 lib64
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 media
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 mnt
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 opt
dr-xr-xr-x 200 root root    0 Jan 17 15:13 proc
drwx------   2 root root 4.0K Dec  4 17:12 root
drwxr-xr-x   1 root root 4.0K Dec 28 23:22 run
drwxr-xr-x   1 root root 4.0K Dec 28 23:22 sbin
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 srv
dr-xr-xr-x  13 root root    0 Dec 20 12:50 sys
drwxrwxrwt   2 root root 4.0K Dec  4 17:12 tmp
drwxr-xr-x   1 root root 4.0K Dec  4 17:11 usr
drwxr-xr-x   1 root root 4.0K Dec  4 17:12 var
-=-
some error message
```

### Description

This route returns the logs for the last execution for the job.

## API - Job stdout

### Request Details

`Method`: `GET`

`URL`: `/tasks/<task-id>/jobs/<job-id>/stdout/`

* `task-id` is the ID for the required task.
* `job-id` is the ID for the required job.

`Body`: -

`Query Parameters`: -

### Example Response

```
total 72K
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 .
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 ..
-rwxr-xr-x   1 root root    0 Jan 17 15:13 .dockerenv
drwxr-xr-x   2 root root 4.0K Dec  4 17:12 bin
drwxr-xr-x   2 root root 4.0K Apr 24  2018 boot
drwxr-xr-x   5 root root  340 Jan 17 15:13 dev
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 etc
drwxr-xr-x   2 root root 4.0K Apr 24  2018 home
drwxr-xr-x   8 root root 4.0K Dec  4 17:11 lib
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 lib64
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 media
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 mnt
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 opt
dr-xr-xr-x 200 root root    0 Jan 17 15:13 proc
drwx------   2 root root 4.0K Dec  4 17:12 root
drwxr-xr-x   1 root root 4.0K Dec 28 23:22 run
drwxr-xr-x   1 root root 4.0K Dec 28 23:22 sbin
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 srv
dr-xr-xr-x  13 root root    0 Dec 20 12:50 sys
drwxrwxrwt   2 root root 4.0K Dec  4 17:12 tmp
drwxr-xr-x   1 root root 4.0K Dec  4 17:11 usr
drwxr-xr-x   1 root root 4.0K Dec  4 17:12 var
```

### Description

This route returns the stdout results for last execution for the job.

## API - Job stderr

### Request Details

`Method`: `GET`

`URL`: `/tasks/<task-id>/jobs/<job-id>/stderr/`

* `task-id` is the ID for the required task.
* `job-id` is the ID for the required job.

`Body`: -

`Query Parameters`: -

### Example Response

```
some error message
```

### Description

This route returns the stderr results for last execution for the job.

## API - Stop Job

### Request Details

`Method`: `POST`

`URL`: `/tasks/<task-id>/jobs/<job-id>/stop/`

* `task-id` is the ID for the required task.
* `job-id` is the ID for the required job.

`Body`: -

`Query Parameters`: -

### Example Response

```
{
  "jobId": "de5fa478-9106-42d6-b142-325941ebf913",
  "jobUrl": "http://localhost:10000/tasks/test-wrkng/jobs/de5fa478-9106-42d6-b142-325941ebf913",
  "taskId": "test-wrkng",
  "taskUrl": "http://localhost:10000/tasks/test-wrkng"
}
```

### Description

This route stops the last execution for this job and if it is a scheduled or recurring job, it cancels the remaining executions (and stops retrying the job).

## API - Retry Job

TBW.

## API - Stream Job Logs

### Request Details

`Method`: `GET`

`URL`: `/tasks/<task-id>/jobs/<job-id>/stream/`

* `task-id` is the ID for the required task;
* `job-id` is the ID for the required job.

`Body`: -

`Query Parameters`: -

### Example Response

-

### Description

This route renders a web page that streams the job's last execution's logs to the browser.

## API - Websocket for Job Logs

### Request Details

`Method`: `GET`

`URL`: `ws://fastlane-server/tasks/<task-id>/jobs/<job-id>/ws/`

* `task-id` is the ID for the required task;
* `job-id` is the ID for the required job.

`Body`: -

`Query Parameters`: -

### Example Response

Websocket connection.

### Description

Connecting to this route using [web sockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) allows users to stream logs for the last execution of the specified job.

A sample script that connects to the websocket route looks like this:

```javascript
// In Javascript
const connect = function() {
  const socket = new WebSocket("ws://fastlane.local:10000/tasks/test-scheduled-task/jobs/19603668-7241-4c50-802f-7c39dac831e6/ws");

  socket.onopen = function (event) {
    console.log('socket open, waiting for logs')
  };

  socket.onmessage = function (event) {
    console.log('Received log', event.data);
  };

  socket.onclose = function (event) {
    console.log('Socket closed');
    if (event.reason != 'done') {
      console.log('Trying again in 5s...');
      if (timeout !== null) {
        clearTimeout(timeout);
        timeout = null;
      }
      timeout = setTimeout(connect, 5000);
    }
  }
}

connect()
```

## API - Job Execution Details

### Request Details

`Method`: `GET`

`URL`: `/tasks/<task-id>/jobs/<job-id>/executions/<execution-id>/`

* `task-id` is the ID for the required task;
* `job-id` is the ID for the required job;
* `execution-id` is the ID for the required job execution.

`Body`: -

`Query Parameters`: -

### Example Response

```json
{
  "execution": {
    "command": "sleep 100", 
    "createdAt": "2019-01-17T17:13:30.924000", 
    "error": "", 
    "executionId": "00735b1e-25c3-467d-a106-05701a786957", 
    "exitCode": 137, 
    "finishedAt": "2019-01-17T17:13:50.136000", 
    "image": "task1", 
    "log": "", 
    "metadata": {
      "container_id": "d432bad154646423369e6fb7a8d46985a1dc0a2612d5b06100357b756781ac6b", 
      "docker_host": "localhost", 
      "docker_port": 1234
    }, 
    "startedAt": "2019-01-17T17:13:34.411000", 
    "status": "failed"
  }, 
  "job": {
    "id": "76903cb5-e7e7-4293-8901-3a7d3344da7c", 
    "url": "http://localhost:10000/tasks/test-wrkng/jobs/76903cb5-e7e7-4293-8901-3a7d3344da7c"
  }, 
  "task": {
    "id": "test-wrkng", 
    "url": "http://localhost:10000/tasks/test-wrkng"
  }
}
```

### Description

This route returns the details for the specified job execution.

## API - Job Execution Logs

### Request Details

`Method`: `GET`

`URL`: `/tasks/<task-id>/jobs/<job-id>/executions/<execution-id>/logs/`

* `task-id` is the ID for the required task;
* `job-id` is the ID for the required job;
* `execution-id` is the ID for the required job execution.

`Body`: -

`Query Parameters`: -

### Example Response

```
total 72K
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 .
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 ..
-rwxr-xr-x   1 root root    0 Jan 17 15:13 .dockerenv
drwxr-xr-x   2 root root 4.0K Dec  4 17:12 bin
drwxr-xr-x   2 root root 4.0K Apr 24  2018 boot
drwxr-xr-x   5 root root  340 Jan 17 15:13 dev
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 etc
drwxr-xr-x   2 root root 4.0K Apr 24  2018 home
drwxr-xr-x   8 root root 4.0K Dec  4 17:11 lib
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 lib64
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 media
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 mnt
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 opt
dr-xr-xr-x 200 root root    0 Jan 17 15:13 proc
drwx------   2 root root 4.0K Dec  4 17:12 root
drwxr-xr-x   1 root root 4.0K Dec 28 23:22 run
drwxr-xr-x   1 root root 4.0K Dec 28 23:22 sbin
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 srv
dr-xr-xr-x  13 root root    0 Dec 20 12:50 sys
drwxrwxrwt   2 root root 4.0K Dec  4 17:12 tmp
drwxr-xr-x   1 root root 4.0K Dec  4 17:11 usr
drwxr-xr-x   1 root root 4.0K Dec  4 17:12 var
-=-
some error
```

### Description

This route returns the stdout and stderr results for the specified job execution, separated by "\n-=-\n".

## API - Job Execution stdout

### Request Details

`Method`: `GET`

`URL`: `/tasks/<task-id>/jobs/<job-id>/executions/<execution-id>/stdout/`

* `task-id` is the ID for the required task;
* `job-id` is the ID for the required job;
* `execution-id` is the ID for the required job execution.

`Body`: -

`Query Parameters`: -

### Example Response

```
total 72K
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 .
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 ..
-rwxr-xr-x   1 root root    0 Jan 17 15:13 .dockerenv
drwxr-xr-x   2 root root 4.0K Dec  4 17:12 bin
drwxr-xr-x   2 root root 4.0K Apr 24  2018 boot
drwxr-xr-x   5 root root  340 Jan 17 15:13 dev
drwxr-xr-x   1 root root 4.0K Jan 17 15:13 etc
drwxr-xr-x   2 root root 4.0K Apr 24  2018 home
drwxr-xr-x   8 root root 4.0K Dec  4 17:11 lib
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 lib64
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 media
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 mnt
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 opt
dr-xr-xr-x 200 root root    0 Jan 17 15:13 proc
drwx------   2 root root 4.0K Dec  4 17:12 root
drwxr-xr-x   1 root root 4.0K Dec 28 23:22 run
drwxr-xr-x   1 root root 4.0K Dec 28 23:22 sbin
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 srv
dr-xr-xr-x  13 root root    0 Dec 20 12:50 sys
drwxrwxrwt   2 root root 4.0K Dec  4 17:12 tmp
drwxr-xr-x   1 root root 4.0K Dec  4 17:11 usr
drwxr-xr-x   1 root root 4.0K Dec  4 17:12 var
```

### Description

This route returns the stdout result for the specified job execution.

## API - Job Execution stderr

`Method`: `GET`

`URL`: `/tasks/<task-id>/jobs/<job-id>/executions/<execution-id>/stderr/`

* `task-id` is the ID for the required task;
* `job-id` is the ID for the required job;
* `execution-id` is the ID for the required job execution.

`Body`: -

`Query Parameters`: -

### Example Response

```
some error
```

### Description

This route returns the stderr result for the specified job execution.

## API - Stop Job Execution

`Method`: `POST`

`URL`: `/tasks/<task-id>/jobs/<job-id>/executions/<execution-id>/stop/`

* `task-id` is the ID for the required task;
* `job-id` is the ID for the required job;
* `execution-id` is the ID for the required job execution.

`Body`: -

`Query Parameters`: -

### Example Response

```
{
  "execution": {
    "id": "d4e20d72-9991-405a-9eb9-d72553204d21", 
    "url": "http://localhost:10000/tasks/task1/jobs/6f4e8b53-95ce-451f-86fb-cd37b8040c42/executions/d4e20d72-9991-405a-9eb9-d72553204d21/"
  }, 
  "job": {
    "id": "6f4e8b53-95ce-451f-86fb-cd37b8040c42", 
    "url": "http://localhost:10000/tasks/task1/jobs/6f4e8b53-95ce-451f-86fb-cd37b8040c42/"
  }, 
  "task": {
    "id": "task1", 
    "url": "http://localhost:10000/tasks/task1/"
  }
}
some error
```

### Description

This route stops a running job execution. If the job is a scheduled (or a CRON) job, this route **WILL NOT** deschedule it. In order to cancel the job scheduling/CRON, you must use the [API - Stop Job](#api-stop-job) route instead.


## API - Stream Job Execution Logs

### Request Details

`Method`: `GET`

`URL`: `/tasks/<task-id>/jobs/<job-id>/stream/executions/<execution-id>/`

* `task-id` is the ID for the required task;
* `job-id` is the ID for the required job;
* `execution-id` is the ID for the required job execution.

`Body`: -

`Query Parameters`: -

### Example Response

-

### Description

This route renders a web page that streams the job execution's logs to the browser.

## API - Websocket for Job Execution Logs

### Request Details

`Method`: `GET`

`URL`: `ws://fastlane-server/tasks/<task-id>/job/<job-id>/executions/<execution-id>/ws/`

* `task-id` is the ID for the required task;
* `job-id` is the ID for the required job;
* `execution-id` is the ID for the required job execution.

`Body`: -

`Query Parameters`: -

### Example Response

Websocket connection.

### Description

Connecting to this route using [web sockets](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API) allows users to stream logs for the specified job execution.

A sample script that connects to the websocket route looks like this:

```javascript
// In Javascript
const connect = function() {
  const socket = new WebSocket("ws://fastlane.local:10000/tasks/test-scheduled-task/jobs/19603668-7241-4c50-802f-7c39dac831e6/executions/96e9d16a-fefc-4764-bb5d-4c1caa6f266c/ws");


  socket.onopen = function (event) {
    console.log('socket open, waiting for logs')
  };

  socket.onmessage = function (event) {
    console.log('Received log', event.data);
  };

  socket.onclose = function (event) {
    console.log('Socket closed');
    if (event.reason != 'done') {
      console.log('Trying again in 5s...');
      if (timeout !== null) {
        clearTimeout(timeout);
        timeout = null;
      }
      timeout = setTimeout(connect, 5000);
    }
  }
}

connect()
```

## API - Healthcheck

### Request Details

`Method`: `GET`

`URL`: `/healthcheck/`

`Body`: -

`Query Parameters`: -

### Example Response

```json
{
  "errors": [],
  "mongo": true,
  "redis": true
}
```

### Description

This route returns `200 OK` if fastlane can connect to MongoDB and Redis.

## API - Farm Status


### Request Details

`Method`: `GET`

`URL`: `/status/`

`Body`: -

`Query Parameters`: -

### Example Response

```json
{
  "containers": {
    "running": []
  }, 
  "hosts": [
    {
      "available": true, 
      "blacklisted": false, 
      "circuit": "closed", 
      "error": null, 
      "host": "localhost", 
      "port": 1234
    }
  ], 
  "jobs": {
    "count": 11, 
    "scheduled": []
  }, 
  "queues": {
    "error": {
      "length": 0
    }, 
    "jobs": {
      "length": 0
    }, 
    "monitor": {
      "length": 0
    }
  }, 
  "tasks": {
    "count": 1
  }
}
```

### Description

This route returns information on the clusters and tasks.

## Workers

TBW.
