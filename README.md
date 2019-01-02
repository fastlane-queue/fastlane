![fastlane](fastlane-logo.png)

[![Build Status](https://travis-ci.org/heynemann/fastlane.svg?branch=master)](https://travis-ci.org/heynemann/fastlane)

![demo](single_task.gif)

## Why [fastlane](https://github.com/fastlane)?

[fastlane](https://github.com/fastlane) is a redis-based queueing service that outsmarts everyone else by using containers.

More seriously, though, [fastlane](https://github.com/fastlane) allows you to easily implement new workers in the form of containers.

Instead of the tedious, repetitive work of yesteryear where you had to implement a worker in language X or Y, you just spin a new container with all the dependencies you require already previously installed, and instruct [fastlane](https://github.com/fastlane) to run a command in that container. Bang! Instant Super-Powered Workers!

## Features

- [x] Ad-Hoc execution of jobs (run job right now);
- [x] Scheduled execution of jobs (run job next sunday at 6am, or run in 10 minutes from now);
- [x] Crontab execution of jobs (run job at "*/10 * * * *" - every ten minutes);
- [x] Additional Job Metadata (useful for webhooks);
- [x] Configurable retries per job;
- [x] Configurable exponential back-off for retries and failures in monitoring of jobs;
- [x] Configurable hard timeout for each execution;
- [x] Route to stop running task;
- [x] Route to retry task;
- [x] Routes to get stdout and stderr for last execution in jobs;
- [x] E-mail subscription to tasks;
- [x] Web hooks on job completion;
- [x] Redact any env that contains blacklisted keywords;
- [ ] Exponential back-off parameters per job;
- [ ] Self-healing handling of interrupted jobs;
- [x] Job log output streaming using WebSockets;
- [x] Workers should handle SIGTERM and exit gracefully;
- [x] [Docker](https://docs.docker.com/) Container Runner (with [docker](https://docs.docker.com/) host pool);
- [x] [Docker](https://docs.docker.com/) Pool per task name (Regular Expressions);
- [x] Rename [docker](https://docs.docker.com/) containers after processing their details;
- [x] Command to prune processed containers;
- [x] Routes to remove/put back [docker](https://docs.docker.com/) host in job balancing;
- [ ] [Docker](https://docs.docker.com/) SSL connections;
- [ ] Circuit breaking when [docker](https://docs.docker.com/) host is unavailable;
- [x] Container Environment Variables per Job;
- [x] Configurable global limit for number of running jobs per task name (Regular Expressions);
- [ ] Limit of concurrent job executions per task;
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

## Getting Started

The team behind [fastlane](https://github.com/fastlane) firmly believes the first 5 minutes with the tool should allow any developer to feel what this tool is all about. So, without further ado let's get some work done.

We assume you have both [docker](https://docs.docker.com/) and [docker-compose](https://docs.docker.com/compose/) properly installed and available.

The first thing, we'll do is get [fastlane](https://github.com/fastlane) up and running (ps: this [docker-compose](https://docs.docker.com/compose/) file runs [Docker In Docker](https://hub.docker.com/_/docker/) and requires privileged mode to run):

```
$ curl https://raw.githubusercontent.com/heynemann/fastlane/master/docker-compose-sample.yml | docker-compose -f - up -d

Starting fastlane...
Creating fastlane_mongo_1       ... done
Creating fastlane_docker-host_1 ... done
Creating fastlane_redis_1       ... done
Creating fastlane_fastlane_1    ... done
fastlane started successfully.
```

After this, both redis (port `10100`), mongo (port `10101`), [docker](https://docs.docker.com/) and [fastlane](https://github.com/fastlane) (port `10000`) should be available. We can confirm it with a `docker ps`:

```
$ docker ps

CONTAINER ID        IMAGE                COMMAND                  CREATED              STATUS              PORTS                      NAMES
64fb69c65437        fastlane             "/bin/sh -c 'honcho …"   About a minute ago   Up About a minute   0.0.0.0:10000->10000/tcp   fastlane_fastlane_1
4c823ea87257        redis                "docker-entrypoint.s…"   About a minute ago   Up About a minute   0.0.0.0:10100->6379/tcp    fastlane_redis_1
d2e8713dce78        docker:stable-dind   "dockerd-entrypoint.…"   About a minute ago   Up About a minute   2375/tcp                   fastlane_docker-host_1
3fa269965f9e        mongo                "docker-entrypoint.s…"   About a minute ago   Up About a minute   0.0.0.0:10101->27017/tcp   fastlane_mongo_1
```

This means that inside our [docker-compose](https://docs.docker.com/compose/) network we can run new containers in the `docker-host` at `docker-host:2375`.

In order to ensure that [fastlane](https://github.com/fastlane) is actually healthy, we can query its `/healthcheck/` route:

```
$ curl http://localhost:10000/healthcheck/

{
  "errors": [],
  "mongo": true,
  "redis": true
}
```

This route ensures [fastlane](https://github.com/fastlane) can access both `redis` and `mongo`. Now let's make sure it can also access our [docker](https://docs.docker.com/) farm:

```
$ curl http://localhost:10000/status/

{
  "containers": {
    "running": []
  },
  "hosts": [
    {
      "blacklisted": false,
      "host": "docker-host:2375"
    }
  ],
  "jobs": {
    "count": 1,
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

The purpose of the `/status/` route is twofold: first, ensure that our farm is able to process jobs, and second to give us some stats on the farm, such as number of jobs and tasks, jobs currently running, blacklisted hosts, etc. 

Now that our [fastlane](https://github.com/fastlane) server is up, let's get our first job done. We'll start the way almost every single programming assignment starts:

```
$ curl -XPOST -d'{"image": "hello-world", "command": "/hello"}' http://localhost:10000/tasks/hello-world

{
  "jobId": "5c2be4b6a69208000b5ebf0e",
  "jobUrl": "http://localhost:10000/tasks/hello-world/jobs/5c2be4b6a69208000b5ebf0e",
  "queueJobId": "c16c474d-f390-4f4c-a4ae-d54c6541470a",
  "taskId": "hello-world",
  "taskUrl": "http://localhost:10000/tasks/hello-world"
}
```

Now with the `jobUrl` we can query the status of our job. If everything went well, our job should have finished after a moment:

```
$ curl http://localhost:10000/tasks/hello-world/jobs/5c2be4b6a69208000b5ebf0e

{
  "job": {
    "createdAt": "2019-01-01T22:07:50.136000",
    "executionCount": 1,
    "executions": [
      {
        "command": "/hello",
        "createdAt": "2019-01-01T22:07:50.180000",
        "error": "",
        "exitCode": 0,
        "finishedAt": "2019-01-01T22:07:58.052000",
        "image": "hello-world",
        "log": "\nHello from Docker!\nThis message shows that your installation appears to be working correctly.\n\nTo generate this message, Docker took the following steps:\n 1. The Docker client contacted the Docker daemon.\n 2. The Docker daemon pulled the \"hello-world\" image from the Docker Hub.\n    (amd64)\n 3. The Docker daemon created a new container from that image which runs the\n    executable that produces the output you are currently reading.\n 4. The Docker daemon streamed that output to the Docker client, which sent it\n    to your terminal.\n\nTo try something more ambitious, you can run an Ubuntu container with:\n $ docker run -it ubuntu bash\n\nShare images, automate workflows, and more with a free Docker ID:\n https://hub.docker.com/\n\nFor more examples and ideas, visit:\n https://docs.docker.com/get-started/\n\n",
        "metadata": {
          "container_id": "dd17020a3d957d11fa5eeaa59d066f2e9f228975c64bb4cef1ce1c74cb50beb8",
          "docker_host": "docker-host",
          "docker_port": "2375"
        },
        "startedAt": "2019-01-01T22:07:52.582000",
        "status": "done"
      }
    ],
    "lastModifiedAt": "2019-01-01T22:07:58.053000",
    "metadata": {
      "enqueued_id": "c16c474d-f390-4f4c-a4ae-d54c6541470a",
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
    "taskId": "hello-world"
  },
  "task": {
    "id": "hello-world",
    "url": "http://localhost:10000/tasks/hello-world"
  }
}
```

That's a lot of details about our job! But the important bits for us are in `job.executions[0].exitCode` and `job.executions[0].log`. Don't worry about the details for now. As a matter of fact, why don't we just see what our job actually wrote to the standard output?

```
$ curl http://localhost:10000/tasks/hello-world/jobs/5c2be4b6a69208000b5ebf0e/stdout

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://hub.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/get-started/
```

Notice we added a `/stdout` to the end of our `jobUrl`? Now that we have accomplished hello world, how about just listing all the files in an ubuntu container?

```
$ curl -XPOST -d'{"image": "ubuntu:latest", "command": "ls -lah /"}' http://localhost:10000/tasks/ubuntu

{
  "jobId": "5c2be641a69208000b5ebf0f",
  "jobUrl": "http://localhost:10000/tasks/ubuntu/jobs/5c2be641a69208000b5ebf0f",
  "queueJobId": "d4c92571-b3c1-4b41-a91b-d550e2b93990",
  "taskId": "ubuntu",
  "taskUrl": "http://localhost:10000/tasks/ubuntu"
}

$ curl http://localhost:10000/tasks/ubuntu/jobs/5c2be641a69208000b5ebf0f/stdout

total 72K
drwxr-xr-x   1 root root 4.0K Jan  1 22:14 .
drwxr-xr-x   1 root root 4.0K Jan  1 22:14 ..
-rwxr-xr-x   1 root root    0 Jan  1 22:14 .dockerenv
drwxr-xr-x   2 root root 4.0K Dec  4 17:12 bin
drwxr-xr-x   2 root root 4.0K Apr 24  2018 boot
drwxr-xr-x   5 root root  340 Jan  1 22:14 dev
drwxr-xr-x   1 root root 4.0K Jan  1 22:14 etc
drwxr-xr-x   2 root root 4.0K Apr 24  2018 home
drwxr-xr-x   8 root root 4.0K Dec  4 17:11 lib
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 lib64
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 media
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 mnt
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 opt
dr-xr-xr-x 343 root root    0 Jan  1 22:14 proc
drwx------   2 root root 4.0K Dec  4 17:12 root
drwxr-xr-x   1 root root 4.0K Dec 28 23:22 run
drwxr-xr-x   1 root root 4.0K Dec 28 23:22 sbin
drwxr-xr-x   2 root root 4.0K Dec  4 17:11 srv
dr-xr-xr-x  13 root root    0 Jan  1 18:38 sys
drwxrwxrwt   2 root root 4.0K Dec  4 17:12 tmp
drwxr-xr-x   1 root root 4.0K Dec  4 17:11 usr
drwxr-xr-x   1 root root 4.0K Dec  4 17:12 var
```

It should be fairly clear by this point that you can send any [docker](https://docs.docker.com/) image and any command and [fastlane](https://github.com/fastlane) will execute it for you, but don't be fooled by its simplicity. This is a very powerful concept, to be able to run anything at a later point in time with an API to query about its status. Never worry about building workers again.

## Installing and Running

### Pre-Requisites

The first and most important requirement is that you have a running [docker](https://docs.docker.com/) Host that accepts HTTP(s) requests. If you have [docker](https://docs.docker.com/) running locally, you probably are set.

In order to use [fastlane](https://github.com/fastlane), you also need to have both MongoDB and Redis instances available. 

**IMPORTANT WARNING**: If you are running fastlane on MacOS, we need to expose [docker](https://docs.docker.com/) host port to our service. This can be achieved by running the following command:

```
$ docker run -d -v /var/run/docker.sock:/var/run/docker.sock -p 127.0.0.1:1234:1234 bobrik/socat TCP-LISTEN:1234,fork UNIX-CONNECT:/var/run/docker.sock
```

This will bridge the port `1234` in the container to the `1234` port in the host and allow us to use the default `localhost:1234` docker host.

### Installing

To install locally, you need python >=3.6.5(preferrably python >=3.7). Just run `pip install fastlane` and you are good to go.

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

In order to ensure that the API is working as expected, open in your browser `http://localhost:10000/healthcheck` and `http://localhost:10000/status`. The first ensures that the API has access to mongo and redis. The second that the [docker](https://docs.docker.com/) farm as well as the queues are working properly.

### Running the Workers

Just run the command:

```
$ fastlane worker -vv
```

## How To?

### How do I run a new job?

This Http `POST` will run an `ubuntu` container and then run the `ls -lah` command, as soon as there's a free working in [fastlane](https://github.com/fastlane).

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

[fastlane](https://github.com/fastlane) supports the well-known [cron format](https://en.wikipedia.org/wiki/Cron). In order to use just specify a `cron` parameter.

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

## Job Options

When creating a new job, this is the most complete body that can be sent:

```json
{
  "image": "ubuntu:latest",
  "command": "ls -lah",
  "envs": {
    "SMTP_SERVER":"my-smtp-server"
  },
  "startIn": "5m",
  "startAt": 1645113692,
  "cron": "* * * * *",
  "metadata": {
    "username": "heynemann",
    "email": "heynemann@some-email.com"
  },
  "notify": {
    "succeeds": ["success@mycompany.com"],
    "fails": ["failure@mycompany.com", "other@mycompany.com"],
    "finishes": ["whatever@mycompany.com"]
  },
  "webhooks": {
    "succeeds": [{
      "url": "http://my.website.com/route",
      "headers": {
        "MY-TOKEN": "qweqwe"
      },
      "retries": 3
    }],
    "fails": [{
      "url": "http://my.website.com/route",
      "headers": {
        "MY-TOKEN": "qweqwe"
      },
      "retries": 3
    }],
    "finishes": [{
      "url": "http://my.website.com/route",
      "headers": {
        "MY-TOKEN": "qweqwe"
      },
      "retries": 3
    }]
  },
  "retries": 4,
  "expiration": 1645113692,
  "timeout": 3600
}
```

* `image` - This parameter specifies the [docker](https://docs.docker.com/) image that should be used to run this job;
* `command` - The command that will be run by the job;
* `envs` - The environment variables that will be set in the container when the job is run;
* `startIn`, `startAt` and `cron` - Different ways to schedule the job. If none of these is passed, the job starts immediately. `startIn` gets a string with how much time in the future to start the job in the form of `2h30m50s`. `startAt` takes an UNIX UTC timestamp that will be used to determine when the job should start. `cron` takes a [cron format](https://en.wikipedia.org/wiki/Cron) string that determines how often this job should be executed;
* `metadata` - This parameter is a dictionary that will be attached to the job's metadata as a `custom` key and can be used to store values that can be later on used by webhooks, as an example;
* `notify` - This parameter specifies cases where the owner of the job wants to be notified by e-mail. This parameter is a dictionary with the `succeeds`, `fails` and `finishes` array keys. In the scenario above, when each job execution succeeds (exit code == 0), `success@mycompany.com` will receive an e-mail with the execution details. When each job execution fails (exit code != 0), `failure@mycompany.com` and `other@mycompany.com` both will receive an e-mail with the execution details. `whatever@mycompany.com` will receive e-mails with the execution details, for all executions of this job, independent of exit code;
* `webhooks` - This parameter specifies cases where the owner of the job wants to dispatch webhooks with the execution details. This parameter is a dictionary with the `succeeds`, `fails` and `finishes` array keys. In the scenario above, when each job execution succeeds (exit code == 0), a `POST` request will be made against `http://my.website.com/rout` with the execution data as `JSON`. `fails` and `finishes` are analogous to the notify option. Only the `url` parameter is required;
* `retries` - This argument determines whether this job should be retried (>0) and how many times. If this argument is not present in the body, retry is disabled;
* `expiration` - If this argument is present, this determines a point in time where this job should not run anymore. It is an UNIX UTC timestamp. The purpose of this argument is for scenarios of high queueing, so the job can sit in the queue for a long time. In this scenario, after a long time, this job might not make sense anymore (i.e.: a push notification);
* `timeout` - This is a timeout in seconds after which the job will be terminated. There's a hard limit in [fastlane](https://github.com/fastlane) and it will use whatever value is lower.

## Architecture

### An example situation

We'll start with an example situation that we can explore in order to understand more about [fastlane](https://github.com/fastlane).

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

[fastlane](https://github.com/fastlane) is by design a system with no authentication and authorization.

Users are responsible for specifying a task id that's globally unique. If two users specify a task with id 'run', their jobs will be grouped together (not an issue for [fastlane](https://github.com/fastlane), since every job has a globally unique id anyways). This might be confusing, though.

The decision here is to sacrifice isolation for simplicity. Usually a queueing system is a backend application, meaning that it's easy enough to construct a front-end for [fastlane](https://github.com/fastlane) that provides authentication and authorization to post jobs in tasks.

### The Container

As said previously, [fastlane](https://github.com/fastlane) uses containers to enable users to have very flexible workers. 

This means that the container must be created and published before creating a new job. And that's the beauty of the system. Never worry about versions of libraries that the worker has to deal with again.

Just pre-install everything you need in the container image, including the application you are running every job cycle, and publish that image to a container repository.

[fastlane](https://github.com/fastlane) supports versioning of containers. You can run the latest version, or just specify a tag to run (`stable` or `0.1.3` for instance).

And that's where `/app/sendmail.py` comes from. It was pre-installed in the container when it was published to the `my.docker.repo.com` container repository.

That also answers the second and third questions. All the dependencies get pre-installed within the container image.

### Tasks, Jobs and Executions in [fastlane](https://github.com/fastlane)

There are three levels in [fastlane](https://github.com/fastlane) hierarchy: tasks, jobs and executions.

Users group their units of work in tasks. Examples of tasks would be "system1-send-mail" or "system2-process-user-registration".

The name of the task is arbitrary and it's not enforced to be unique. It's advised to use a task name that includes your system name as to ensure uniqueness.

Jobs are created every time a task is enqueued. A job indicates whether it's scheduled and is basically a container for all the executions inside it.

A Job Execution is the actual unit of work. An execution has an image, a command and any other metadata that is required to run the unit of work.

Why aren't these details in the Job, instead of the execution? Because we can have many executions for a single job: Cron and retries are good examples of this behavior.

### Jobs Lifecycle

TBW.

## Docker Executor

The [docker](https://docs.docker.com/) executor features a pool of [docker](https://docs.docker.com/) hosts that execute commands for you.

### Pool Configuration

Configuring the pool is done with the `DOCKER_HOSTS` configuration. It is a JSON-encoded string that specifies the logical farms of [docker](https://docs.docker.com/) hosts.

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

### [Docker](https://docs.docker.com/) Executor Blacklisting

In order to improve on reliability and at the same time allow for fast and safe upgrades of [docker](https://docs.docker.com/) hosts, [fastlane](https://github.com/fastlane) comes bundled with a route for blacklisting [docker](https://docs.docker.com/) hosts.

The use case for this blacklist is as follows:

* `POST` to the http://fastlane.local:10000/docker-executor/blacklist with a body of `{"host": "docker-host1.company.com:1234"}`;
* Now the blacklisted host will not receive any new jobs;
* Wait for all the running jobs to finish;
* Upgrade, change, do anything that needs to be done with the host and get it back online;
* `DEL` to the http://fastlane.local:10000/docker-executor/blacklist with a body of `{"host": "docker-host1.company.com:1234"}`.

Then do the same for all the other hosts.

**WARNING**: Please ensure that at least one [docker](https://docs.docker.com/) host is available and **NOT** blacklisted in each farm. If all hosts are blacklisted, [fastlane](https://github.com/fastlane) will start dropping jobs on the affected farms.

## API

### Http API

TBW.

### Workers

TBW.

## Configuration

TBW.

## Contributing

Logo was created using https://logomakr.com/4xwJMs.
