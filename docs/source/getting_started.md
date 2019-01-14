# Getting Started

The team behind [fastlane](https://github.com/fastlane) firmly believes the first 5 minutes with the tool should allow any developer to feel what this tool is all about. So, without further ado let's get some work done.

We assume you have both [docker](https://docs.docker.com/) and [docker-compose](https://docs.docker.com/compose/) properly installed and available.

## Requirements

The first thing, we'll do is get [fastlane](https://github.com/fastlane) up and running (ps: this [docker-compose](https://docs.docker.com/compose/) file runs [Docker In Docker](https://hub.docker.com/_/docker/) and requires privileged mode to run):

```bash
$ curl https://raw.githubusercontent.com/heynemann/fastlane/master/docker-compose-sample.yml | docker-compose -f - up -d

Starting fastlane...
Creating fastlane_mongo_1       ... done
Creating fastlane_docker-host_1 ... done
Creating fastlane_redis_1       ... done
Creating fastlane_fastlane_1    ... done
fastlane started successfully.
```

After this, both [redis](https://redis.io/) (port `10100`), [Mongo DB](https://www.mongodb.com/) (port `10101`), [docker](https://docs.docker.com/) and [fastlane](https://github.com/fastlane) (port `10000`) should be available. We can confirm it with a `docker ps`:

```bash
$ docker ps

CONTAINER ID        IMAGE                COMMAND                  CREATED              STATUS              PORTS                      NAMES
64fb69c65437        fastlane             "/bin/sh -c 'honcho …"   About a minute ago   Up About a minute   0.0.0.0:10000->10000/tcp   fastlane_fastlane_1
4c823ea87257        redis                "docker-entrypoint.s…"   About a minute ago   Up About a minute   0.0.0.0:10100->6379/tcp    fastlane_redis_1
d2e8713dce78        docker:stable-dind   "dockerd-entrypoint.…"   About a minute ago   Up About a minute   2375/tcp                   fastlane_docker-host_1
3fa269965f9e        mongo                "docker-entrypoint.s…"   About a minute ago   Up About a minute   0.0.0.0:10101->27017/tcp   fastlane_mongo_1
```

This means that inside our [docker-compose](https://docs.docker.com/compose/) network we can run new containers in the `docker-host` at `docker-host:2375`.

## Healthcheck and Status

In order to ensure that [fastlane](https://github.com/fastlane) is actually healthy, we can query its `/healthcheck/` route:

```bash
$ curl http://localhost:10000/healthcheck/
```

```json
{
  "errors": [],
  "mongo": true,
  "redis": true
}
```

This route ensures [fastlane](https://github.com/fastlane) can access both [redis](https://redis.io/) and [Mongo DB](https://www.mongodb.com/). Now let's make sure it can also access our [docker](https://docs.docker.com/) farm:

```bash
$ curl http://localhost:10000/status/
```

```json
{
  "containers": {
    "running": []
  },
  "hosts": [
    {
      "available": true,
      "blacklisted": false,
      "error": null,
      "host": "docker-host:2375"
    }
  ],
  "jobs": {
    "count": 0,
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
    "count": 0
  }
}
```

The purpose of the `/status/` route is twofold: first, ensure that our farm is able to process jobs, and second to give us some stats on the farm, such as number of jobs and tasks, jobs currently running, blacklisted hosts, etc. 

## Our first job

Now that our [fastlane](https://github.com/fastlane) server is up, let's get our first job done. We'll start the way almost every single programming assignment starts:

```bash
$ curl -XPOST -d'{"image": "hello-world", "command": "/hello"}' http://localhost:10000/tasks/hello-world
```

```json
{
  "jobId": "5c2be4b6a69208000b5ebf0e",
  "jobUrl": "http://localhost:10000/tasks/hello-world/jobs/5c2be4b6a69208000b5ebf0e",
  "queueJobId": "c16c474d-f390-4f4c-a4ae-d54c6541470a",
  "taskId": "hello-world",
  "taskUrl": "http://localhost:10000/tasks/hello-world"
}
```

Now with the `jobUrl` we can query the status of our job. If everything went well, our job should have finished after a moment:

    $ curl http://localhost:10000/tasks/hello-world/jobs/5c2be4b6a69208000b5ebf0e

```json
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

Notice we added a `/stdout` to the end of our `jobUrl`?

## Let's get real

Now that we have accomplished `hello world`, how about just listing all the files in an ubuntu container?

    $ curl -XPOST -d'{"image": "ubuntu:latest", "command": "ls -lah /"}' http://localhost:10000/tasks/ubuntu

```json
{
  "jobId": "5c2be641a69208000b5ebf0f",
  "jobUrl": "http://localhost:10000/tasks/ubuntu/jobs/5c2be641a69208000b5ebf0f",
  "queueJobId": "d4c92571-b3c1-4b41-a91b-d550e2b93990",
  "taskId": "ubuntu",
  "taskUrl": "http://localhost:10000/tasks/ubuntu"
}
```

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

## Conclusion

It should be fairly clear by this point that you can send any [docker](https://docs.docker.com/) image and any command and [fastlane](https://github.com/fastlane) will execute it for you.

Don't be fooled by its simplicity. This is a very powerful concept, to be able to run anything at a later point in time with an API to query about its status.

Never worry about building workers again.
