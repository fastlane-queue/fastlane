![fastlane](source/_static/fastlane-logo.png)

![demo](source/_static/single_task.gif)

## Why Fastlane?

fastlane is a redis-based queueing service that outsmarts everyone else by using containers.

More seriously, though, fastlane allows you to easily implement new workers in the form of containers.

Instead of the tedious, repetitive work of yesteryear where you had to implement a worker in language X or Y, you just spin a new container with all the dependencies you require already previously installed, and instruct fastlane to run a command in that container. Bang! Instant Super-Powered Workers!

## Features

- [x] Ad-Hoc execution of jobs (run job right now);
- [x] Scheduled execution of jobs (run job next sunday at 6am, or run in 10 minutes from now);
- [x] Crontab execution of jobs (run job at "*/10 * * * *" - every ten minutes);
- [x] Configurable retries per job;
- [x] Configurable exponential back-off for retries and failures in monitoring of jobs;
- [x] Configurable hard timeout for each execution;
- [x] Route to stop running task;
- [x] Route to retry task;
- [x] Routes to get stdout and stderr for last execution in jobs;
- [ ] E-mail subscription to tasks;
- [ ] Web hooks on job completion;
- [x] Redact any env that contains blacklisted keywords;
- [ ] Exponential back-off parameters per job;
- [ ] Self-healing handling of interrupted jobs;
- [x] Job log output streaming using WebSockets;
- [x] Workers should handle SIGTERM and exit gracefully;
- [x] Docker Container Runner (with Docker Host Pool);
- [x] Docker Pool per task name (Regular Expressions);
- [ ] Docker SSL connections;
- [ ] Circuit breaking when Docker Host is unavailable;
- [x] Container Environment Variables per Job;
- [x] Configurable global limit for number of running jobs per task name (Regular Expressions);
- [ ] Kubernetes Container Runner;
- [x] MongoDB Task and Job Storage;
- [x] Structured Logging;
- [x] Monitoring of job completion;
- [x] Job Expiration;
- [x] Stop a recurring job;
- [x] API to retrieve job and task details;
- [x] Status Page with details on the farm status (executors, scheduled tasks and queue sizes);
- [x] Error handling mechanism (Sentry built-in, extensible)
- [ ] Usage metrics (extensible);
- [ ] Support Redis, Redis Sentinel and Redis Cluster;
- [ ] Admin to inspect tasks and jobs;
- [ ] Admin to inspect health of queueing system (error queue, size of queues, etc).

## Installing and Running

### Pre-Requisites

TBW.

### Running the API

TBW.

### Running the Workers

TBW.

## How To?

### How do I run a new job?

This Http `POST` will run an `ubuntu` container and then run the `ls -lah` command, as soon as there's a free working in fastlane.

```
$ curl -XPOST -d'{"image": "ubuntu:latest", "command": "ls -lah"}' http://fastlane.local:10000/tasks/test-task
{
  "taskId": "test-task",
  "jobId": "5c094abcedc7d5be820e20da",
  "queueJobId": "db72db9b-cb49-44bd-b2fa-b3afc8e3a041",
  "jobUrl": "http://fastlane.local:10000/tasks/test-task/jobs/5c094abcedc7d5be820e20da",
  "taskUrl": "http://fastlane.local:10000/tasks/test-task"
}
```

In order to find more about the running (or done by now) job, just follow the `jobUrl` parameter of the returned JSON.

### How do I run a new job at a specific point in the future?

This Http `POST` will run an `ubuntu` container and then run the `ls -lah` command, at Thursday, February 17, 2022 4:01:32 PM GMT.

```
$ curl -XPOST -d'{"image": "ubuntu:latest", "command": "ls -lah", "startAt": 1645113692}' http://fastlane.local:10000/tasks/test-scheduled-task
{
  "taskId": "test-scheduled-task",
  "jobId": "5c094abcedc7d5be820e20da",
  "queueJobId": "db72db9b-cb49-44bd-b2fa-b3afc8e3a041",
  "jobUrl": "http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da",
  "taskUrl": "http://fastlane.local:10000/tasks/test-scheduled-task"
}
```

In order to find more about the running (or done by now) job, just follow the `jobUrl` parameter of the returned JSON.

### How do I run a new job in 5 minutes?

This Http `POST` will run an `ubuntu` container and then run the `ls -lah` command, in 5 minutes.

```
$ curl -XPOST -d'{"image": "ubuntu:latest", "command": "ls -lah", "startIn": "5m"}' http://fastlane.local:10000/tasks/test-scheduled-task
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

### How do I run a job periodically? 

Fastlane supports the well-known [cron format](https://en.wikipedia.org/wiki/Cron). In order to use just specify a `cron` parameter.

This Http `POST` will run an `ubuntu` container and then run the `ls -lah` command, every each minute of every hour, every day.

```
$ curl -XPOST -d'{"image": "ubuntu:latest", "command": "ls -lah", "cron": "* * * * *"}' http://fastlane.local:10000/tasks/test-scheduled-task
{
  "taskId": "test-scheduled-task",
  "jobId": "5c094abcedc7d5be820e20da",
  "queueJobId": "db72db9b-cb49-44bd-b2fa-b3afc8e3a041",
  "jobUrl": "http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da",
  "taskUrl": "http://fastlane.local:10000/tasks/test-scheduled-task"
}
```

Just a reminder of the cron format:

```
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of the month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday;
# │ │ │ │ │                                   7 is also Sunday on some systems)
# │ │ │ │ │
# │ │ │ │ │
# * * * * * command to execute
```

In order to find more about the running (or done by now) job, just follow the `jobUrl` parameter of the returned JSON.

### How do I stop a periodical job?

Just `POST` to the job URL with a `/stop` suffix in the job's URL.

```
$ curl -XPOST http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da/stop
```

### How do I find all the jobs in my task?

Just do a `GET` on the task URL, like:

```
$ curl -XPOST http://fastlane.local:10000/tasks/test-my-task
```

### How do I get stdout and stderr data for an execution after it finishes?

You can query both after the job id. The exit code comes as a header called `Fastlane-Exit-Code`.

```
$ curl http://fastlane.local:10000/tasks/test-my-task/jobs/5c094abcedc7d5be820e20da/stdout

# and

$ curl http://fastlane.local:10000/tasks/test-my-task/jobs/5c094abcedc7d5be820e20da/stderr
```


### How do I see what's going on with my job before it finishes?

Fastlane comes equipped with two routes for that purpose: `/task/<task-id>/jobs/<job-id>/stream` and `/task/<task-id>/jobs/<job-id>/ws`.

The former is a simple page that connects to the latter using WebSockets. That means you should open it in your browser. Just navigate to `http://fastlane.local:10000/tasks/test-scheduled-task/jobs/5c094abcedc7d5be820e20da/stream`.

To integrate with Fastlane and stream the results of a job, just connect to it using Websockets like:

```
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

## Architecture

### An example situation

We'll start with an example situation that we can explore in order to understand more about fastlane.

Let's say I want to run a job that sends an e-mail when something happens and I have a container already configured with templates and all I need to pass is the SMTP as an env variable and a command to execute a python script:

```
$ curl -XPOST --header "Content-Type: application/json" -d'{"image": "my.docker.repo.com/my-send-email-image:latest", "command": "python /app/sendmail.py", "envs": {"SMTP_SERVER":"my-smtp-server"}}' http://fastlane.local:10000/tasks/send-very-specific-email
{
    "taskId": "send-very-specific-email",
    "jobId": "5b8db248edc7d584132a6d4d",
    "queueJobId": "77cfabbb-1864-4073-afe7-0efe01014754"
}
```

In this request I'm creating/updating a task called `send-very-specific-email` and creating a new job in it to execute the command `python /app/sendmail.py`. I hope you now have a **boatload** of questions, like:

* Where did you get `/app/sendmail.py` from?
* What version of the python interpreter are you running? Are you even sure python is installed?
* What about the python and system libraries that `sendmail.py` depends on? When were they installed?
* What is that jobId in the return of the `POST` and how do I use that?
* What does it mean for that job to be in a queue? I thought you said that Ad-Hoc execution meant running the job **right now**!

We'll address these now.

### Design Decisions

fastlane is by design a system with no authentication and authorization.

Users are responsible for specifying a task id that's globally unique. If two users specify a task with id 'run', their jobs will be grouped together (not an issue for fastlane, since every job has a globally unique id anyways). This might be confusing, though.

The decision here is to sacrifice isolation for simplicity. Usually a queueing system is a backend application, meaning that it's easy enough to construct a front-end for fastlane that provides authentication and authorization to post jobs in tasks.

### The Container

As said previously, fastlane uses containers to enable users to have very flexible workers. 

This means that the container must be created and published before creating a new job. And that's the beauty of the system. Never worry about versions of libraries that the worker has to deal with again.

Just pre-install everything you need in the container image, including the application you are running every job cycle, and publish that image to a container repository.

fastlane supports versioning of containers. You can run the latest version, or just specify a tag to run (`stable` or `0.1.3` for instance).

And that's where `/app/sendmail.py` comes from. It was pre-installed in the container when it was published to the `my.docker.repo.com` container repository.

That also answers the second and third questions. All the dependencies get pre-installed within the container image.

### Tasks, Jobs and Executions in fastlane

There are three levels in fastlane hierarchy: tasks, jobs and executions.

Users group their units of work in tasks. Examples of tasks would be "system1-send-mail" or "system2-process-user-registration".

The name of the task is arbitrary and it's not enforced to be unique. It's advised to use a task name that includes your system name as to ensure uniqueness.

Jobs are created every time a task is enqueued. A job indicates whether it's scheduled and is basically a container for all the executions inside it.

A Job Execution is the actual unit of work. An execution has an image, a command and any other metadata that is required to run the unit of work.

Why aren't these details in the Job, instead of the execution? Because we can have many executions for a single job: Cron and retries are good examples of this behavior.

### Jobs Lifecycle

TBW.

## API

### Http API

TBW.

### Workers

TBW.

## Configuration

TBW.

## Contributing

Logo was created using https://logomakr.com/4xwJMs.
