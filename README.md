![fastlane](fastlane-logo.png)

![demo](single_task.gif)

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
- [x] E-mail subscription to tasks;
- [ ] Web hooks on job completion;
- [x] Redact any env that contains blacklisted keywords;
- [ ] Exponential back-off parameters per job;
- [ ] Self-healing handling of interrupted jobs;
- [x] Job log output streaming using WebSockets;
- [x] Workers should handle SIGTERM and exit gracefully;
- [x] Docker Container Runner (with Docker Host Pool);
- [x] Docker Pool per task name (Regular Expressions);
- [x] Routes to remove/put back Docker Host in job balancing;
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
- [x] Support Redis and Redis Sentinel;
- [ ] Support Redis Cluster;
- [ ] Admin to inspect tasks and jobs.

## Installing and Running

### Pre-Requisites

The first and most important requirement is that you have a running Docker Host that accepts HTTP(s) requests. If you have docker running locally, you probably are set.

In order to use fastlane, you also need to have both MongoDB and Redis instances available. If you just want to test fastlane and you have [Docker Compose]() available, run the following command:

```
$ curl https://raw.githubusercontent.com/heynemann/fastlane/master/docker-compose-sample.yml | docker-compose -f - up -d

Creating tmp_redis_1 ... done
Creating tmp_mongo_1 ... done

```

After this, both redis and mongo should be available at ports `10100` and `10101` respectively. We can confirm it with a `docker ps`:

```
$ docker ps

CONTAINER ID        IMAGE               COMMAND                  CREATED              STATUS              PORTS                      NAMES
d1a120f05601        redis               "docker-entrypoint.s…"   About a minute ago   Up About a minute   0.0.0.0:10100->6379/tcp    tmp_redis_1
52a46e244b28        mongo               "docker-entrypoint.s…"   About a minute ago   Up About a minute   0.0.0.0:10101->27017/tcp   tmp_mongo_1
```

**IMPORTANT WARNING**: If you are running fastlane on MacOS, we need to expose Docker Host port to our service. This can be achieved by running the following command:

```
$ docker run -d -v /var/run/docker.sock:/var/run/docker.sock -p 127.0.0.1:1234:1234 bobrik/socat TCP-LISTEN:1234,fork UNIX-CONNECT:/var/run/docker.sock
```

This will bridge the port `1234` in the container to the `1234` port in the host and allow us to use the default `localhost:1234` docker host.

### Installing

To install locally, you need python 3.7+. Just run `pip install fastlane` and you are good to go.

### Running the API

Just run the command:

```
$ fastlane api -vvv
```

Optionally you can generate a configuration file and pass it in:

```
$ fastlane config > my.conf

$ fastlane api -vvv -c my.conf
```

In order to ensure that the API is up and running, open in your browser `http://localhost:10000/healthcheck` and `http://localhost:10000/status`. The first ensures that the API has access to mongo and redis. The second that the docker farm as well as the queues are working properly.

### Running the Workers

Just run the command:

```
$ fastlane worker -vv
```

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

## Job Options

When creating a new job, this is the most complete body that can be sent:

```
{
  "image": "ubuntu:latest",
  "command": "ls -lah",
  "envs": {
    "SMTP_SERVER":"my-smtp-server"
  },
  "startIn": "5m",
  "startAt": 1645113692,
  "cron": "* * * * *",
  "notify": {
    "succeeds": ["success@mycompany.com"],
    "fails": ["failure@mycompany.com", "other@mycompany.com"],
    "finishes": ["whatever@mycompany.com"]
  },
  "retries": 4,
  "expiration": 1645113692,
  "timeout": 3600
}
```

* `image` - This parameter specifies the docker image that should be used to run this job;
* `command` - The command that will be run by the job;
* `envs` - The environment variables that will be set in the container when the job is run;
* `startIn`, `startAt` and `cron` - Different ways to schedule the job. If none of these is passed, the job starts immediately. `startIn` gets a string with how much time in the future to start the job in the form of `2h30m50s`. `startAt` takes an UNIX UTC timestamp that will be used to determine when the job should start. `cron` takes a [cron format](https://en.wikipedia.org/wiki/Cron) string that determines how often this job should be executed;
* `notify` - This parameter specifies cases where the owner of the job wants to be notified by e-mail. This parameter is a dictionary with the `succeeds`, `fails` and `finishes` array keys. In the scenario above, when each job execution succeeds (exit code == 0), `success@mycompany.com` will receive an e-mail with the execution details. When each job execution fails (exit code != 0), `failure@mycompany.com` and `other@mycompany.com` both will receive an e-mail with the execution details. `whatever@mycompany.com` will receive e-mails with the execution details, for all executions of this job, independent of exit code;
* `retries` - This argument determines whether this job should be retried (>0) and how many times. If this argument is not present in the body, retry is disabled;
* `expiration` - If this argument is present, this determines a point in time where this job should not run anymore. It is an UNIX UTC timestamp. The purpose of this argument is for scenarios of high queueing, so the job can sit in the queue for a long time. In this scenario, after a long time, this job might not make sense anymore (i.e.: a push notification);
* `timeout` - This is a timeout in seconds after which the job will be terminated. There's a hard limit in Fastlane and it will use whatever value is lower.

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

## Docker Executor

The docker executor features a pool of docker hosts that execute commands for you.

### Pool Configuration

Configuring the pool is done with the `DOCKER_HOSTS` configuration. It is a JSON-encoded string that specifies the logical farms of docker hosts.

An example configuration with two pools:

```
DOCKER_HOSTS = "[
  {"match": "producta.+", "hosts": ["docker-host1.company.com", "docker-host2.company.com"], "maxRunning": 10},
  {"match": "productb.+", "hosts": ["docker-host5.company.com", "docker-host6.company.com"], "maxRunning": 20},
  {"match": "", "hosts": ["docker-host3.company.com", "docker-host4.company.com"], "maxRunning": 10}
]"
```

This configuration ensures that any tasks whose id start with `producta` like `producta-send-notifications` end up in a farm with the `docker-host1.company.com` and `docker-host2.company.com` hosts. If, on the other hand, the task id starts with `productb` then the job will run in the farm with the `docker-host5.company.com` and `docker-host6.company.com` hosts. Any other task id's will be executed in the farm with the `docker-host3.company.com` and `docker-host4.company.com` hosts.

The `maxRunning` parameter indicates how many concurrent jobs can be run in the farm.

### Docker Executor Blacklisting

In order to improve on reliability and at the same time allow for fast and safe upgrades of docker hosts, Fastlane comes bundled with a route for blacklisting docker hosts.

The use case for this blacklist is as follows:

* `POST` to the http://fastlane.local:10000/docker-executor/blacklist with a body of `{"host": "docker-host1.company.com:1234"}`;
* Now the blacklisted host will not receive any new jobs;
* Wait for all the running jobs to finish;
* Upgrade, change, do anything that needs to be done with the host and get it back online;
* `DEL` to the http://fastlane.local:10000/docker-executor/blacklist with a body of `{"host": "docker-host1.company.com:1234"}`.

Then do the same for all the other hosts.

**WARNING**: Please ensure that at least one docker host is available and **NOT** blacklisted in each farm. If all hosts are blacklisted, Fastlane will start dropping jobs on the affected farms.

## API

### Http API

TBW.

### Workers

TBW.

## Configuration

TBW.

## Contributing

Logo was created using https://logomakr.com/4xwJMs.
