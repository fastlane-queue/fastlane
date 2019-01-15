# Installing and Running

## Pre-Requisites

The first and most important requirement is that you have a running [docker](https://docs.docker.com/) host that accepts HTTP(s) requests. If you have [docker](https://docs.docker.com/) running locally, you probably are set.

In order to use [fastlane](https://github.com/heynemann/fastlane), you also need to have both [Mongo DB](https://www.mongodb.com/) and [Redis](https://redis.io/) instances available. 

**IMPORTANT WARNING**: If you are running fastlane on MacOS, you must expose [docker](https://docs.docker.com/) host port to [fastlane](https://github.com/heynemann/fastlane). This can be achieved by running the following command:

    $ docker run -d -v /var/run/docker.sock:/var/run/docker.sock -p 127.0.0.1:1234:1234 bobrik/socat TCP-LISTEN:1234,fork UNIX-CONNECT:/var/run/docker.sock

This will bridge the port `1234` in the container to the `1234` port in the host and allow us to use the default `localhost:1234` docker host.

## Installing

To install locally, you need python >=3.6.5(preferrably python >=3.7). Just run `pip install fastlane` and you are good to go.

## Required Services

[fastlane](https://github.com/heynemann/fastlane) is divided in two different parts: `API` and `Worker`.

The `API` is responsible for receiving requests for new jobs, as well as providing task and job metadata.

The `Worker` is responsible for starting and monitoring jobs in the [docker](https://docs.docker.com/) farm.

## Configuration

Both the `API` and the `Worker` can use the same configuration file. In order to get a sample configuration file that you can modify, run the following command:

    $ fastlane config > my.conf

To configure [Mongo DB](https://www.mongodb.com/), we can change the `MONGODB_CONFIG`, or set it via environment variable.

```python
MONGODB_CONFIG = {
    "host": "mongodb://localhost:10101/fastlane",
    "db": "fastlane",
    "serverSelectionTimeoutMS": 100,
    "connect": false
}
```

In order to connect to [Redis](https://redis.io/), we must supply a valid connection url (either in configuration file or environment variable), likt this:

```python
REDIS_URL = 'redis://localhost:10100/0'
```

Last but not least, you must configure your [docker](https://docs.docker.com/) farm using the `DOCKER_HOSTS` configuration variable (or environment variable):

```python
DOCKER_HOSTS = [
    {
        "match": "",
        "hosts": ["localhost:2375"],
        "maxRunning":2
    }
]
```

This configuration specifies that for all tasks with some `task_id` that matches the `match` configuration, these are the docker hosts that should be used, as well the maximum number of running containers that should be used. Another configuration might look like:

```python
DOCKER_HOSTS = [
    {
        "match": "task-system1-.+",
        "hosts": ["system1.docker.mycompany.com:2375"],
        "maxRunning": 20
    },
    {
        "match": "task-system2-.+",
        "hosts": ["system2.docker.mycompany.com:2375"],
        "maxRunning": 20
    },
]
```

This configuration only allows tasks that start with `task-system1-` or `task-system2-`. Any other tasks won't be run. The empty match is a match-all case.

## Running the API

    $ fastlane api -vvv -c my.conf

In order to ensure that the API is working as expected, open in your browser `http://localhost:10000/healthcheck` and `http://localhost:10000/status`. The first ensures that the API has access to [Mongo DB](https://www.mongodb.com/) and [redis](https://redis.io/). The second that the [docker](https://docs.docker.com/) farm as well as the queues are working properly.

The `API` log is structured as JSON. For more details type `fastlane worker --help`.

## Running the Workers

Just run the command:

    $ fastlane worker -vvv -c my.conf

The worker command has options to define which queues it should monitor. This enabled users to scale each queue independently (jobs, monitor, etc.).

After this command, jobs should be running. The `Worker` log is structured as JSON. For more details type `fastlane worker --help`.
