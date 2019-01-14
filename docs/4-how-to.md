# 4 how to

## How do I run a new job?

This Http `POST` will run an `ubuntu` container and then run the `ls -lah` command, as soon as there's a free working in [fastlane](https://github.com/fastlane).

    $ curl -XPOST -d'{"image": "ubuntu:latest", "command": "ls -lah"}' http://fastlane.local:10000/tasks/test-task

```json
    {
      "taskId": "test-task",
      "jobId": "5c094abcedc7d5be820e20da",
      "queueJobId": "db72db9b-cb49-44bd-b2fa-b3afc8e3a041",
      "jobUrl": "http://fastlane.local:10000/tasks/test-task/jobs/5c094abcedc7d5be820e20da",
      "taskUrl": "http://fastlane.local:10000/tasks/test-task"
    }
```

In order to find more about the running (or done by now) job, just follow the `jobUrl` parameter of the returned JSON.

## How do I run a new job at a specific point in the future?

This Http `POST` will run an `ubuntu` container and then run the `ls -lah` command, at Thursday, February 17, 2022 4:01:32 PM GMT.

    $ curl -XPOST -d'{"image": "ubuntu:latest", "command": "ls -lah", "startAt": 1645113692}' http://fastlane.local:10000/tasks/test-scheduled-task

```json
    {
      "taskId": "test-scheduled-task",
      "jobId": "5c094abcedc7d5be820e20da",
      "queueJobId": "db72db9b-cb49-44bd-b2fa-b3afc8e3a041",
      "jobUrl": "http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da",
      "taskUrl": "http://fastlane.local:10000/tasks/test-scheduled-task"
    }
```

In order to find more about the running (or done by now) job, just follow the `jobUrl` parameter of the returned JSON.

## How do I run a new job in 5 minutes?

This Http `POST` will run an `ubuntu` container and then run the `ls -lah` command, in 5 minutes.

    $ curl -XPOST -d'{"image": "ubuntu:latest", "command": "ls -lah", "startIn": "5m"}' http://fastlane.local:10000/tasks/test-scheduled-task

```json
    {
      "taskId": "test-scheduled-task",
      "jobId": "5c094abcedc7d5be820e20da",
      "queueJobId": "db72db9b-cb49-44bd-b2fa-b3afc8e3a041",
      "jobUrl": "http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da",
      "taskUrl": "http://fastlane.local:10000/tasks/test-scheduled-task"
    }
```

Supported formats also include: `10s`, `2m30s`, `4h30m25s`, `2h30m`, `240h`.

In order to find more about the running (or done by now) job, just follow the `jobUrl` parameter of the returned JSON.

## How do I run a job periodically?

[fastlane](https://github.com/fastlane) supports the well-known [cron format](https://en.wikipedia.org/wiki/Cron). In order to use just specify a `cron` parameter.

This Http `POST` will run an `ubuntu` container and then run the `ls -lah` command, every each minute of every hour, every day.

    $ curl -XPOST -d'{"image": "ubuntu:latest", "command": "ls -lah", "cron": "* * * * *"}' http://fastlane.local:10000/tasks/test-scheduled-task

```json
    {
      "taskId": "test-scheduled-task",
      "jobId": "5c094abcedc7d5be820e20da",
      "queueJobId": "db72db9b-cb49-44bd-b2fa-b3afc8e3a041",
      "jobUrl": "http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da",
      "taskUrl": "http://fastlane.local:10000/tasks/test-scheduled-task"
    }
```

Just a reminder of the cron format:

    # ┌───────────── minute (0 - 59)
    # │ ┌───────────── hour (0 - 23)
    # │ │ ┌───────────── day of the month (1 - 31)
    # │ │ │ ┌───────────── month (1 - 12)
    # │ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday;
    # │ │ │ │ │                                   7 is also Sunday on some systems)
    # │ │ │ │ │
    # │ │ │ │ │
    # * * * * * command to execute

In order to find more about the running (or done by now) job, just follow the `jobUrl` parameter of the returned JSON.

## How do I stop a periodical job?

Just `POST` to the job URL with a `/stop` suffix in the job's URL.

    $ curl -XPOST http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da/stop

## How do I find all the jobs in my task?

Just do a `GET` on the task URL, like:

    $ curl -XPOST http://fastlane.local:10000/tasks/test-my-task

## How do I get stdout and stderr data for an execution after it finishes?

You can query both after the job id. The exit code comes as a header called `Fastlane-Exit-Code`.

    $ curl http://fastlane.local:10000/tasks/test-my-task/jobs/5c094abcedc7d5be820e20da/stdout

    # and

    $ curl http://fastlane.local:10000/tasks/test-my-task/jobs/5c094abcedc7d5be820e20da/stderr

## How do I see what's going on with my job before it finishes?

[fastlane](https://github.com/fastlane) comes equipped with two routes for that purpose: `/task/<task-id>/jobs/<job-id>/stream` and `/task/<task-id>/jobs/<job-id>/ws`.

The former is a simple page that connects to the latter using WebSockets. That means you should open it in your browser. Just navigate to `http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da/stream`.

To integrate with [fastlane](https://github.com/fastlane) and stream the results of a job, just connect to it using Websockets like:

```javascript
// In Javascript
const connect = function() {
  const socket = new WebSocket("ws://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da/ws");

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

The reason when the socket gets closed tells you what happened. If the reason is `retry` it means you should reconnect (like the above) since the job has not started or not finished yet. If the reason is `done` it means you are done and should not reconnect.
