![fastlane](fastlane-logo.svg)

[![github repo](https://img.shields.io/badge/github-repo-blue.svg)](https://github.com/fastlane-queue/fastlane) [![Build Status](https://travis-ci.org/fastlane-queue/fastlane.svg?branch=master)](https://travis-ci.org/fastlane-queue/fastlane) [![Codacy Badge](https://api.codacy.com/project/badge/Coverage/f1325bf0a8e8419692487d3b5d2fa36b)](https://www.codacy.com/app/heynemann/fastlane?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=fastlane-queue/fastlane&amp;utm_campaign=Badge_Coverage) [![Docs](https://readthedocs.org/projects/fastlane/badge/?version=latest)](https://fastlane.readthedocs.io/en/latest/?badge=latest) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/f1325bf0a8e8419692487d3b5d2fa36b)](https://www.codacy.com/app/heynemann/fastlane?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=fastlane-queue/fastlane&amp;utm_campaign=Badge_Grade) [![BCH compliance](https://bettercodehub.com/edge/badge/fastlane-queue/fastlane?branch=master)](https://bettercodehub.com/results/fastlane-queue/fastlane) [![Issues](https://img.shields.io/github/issues/fastlane-queue/fastlane.svg)](https://github.com/fastlane-queue/fastlane/issues)

[![demo](https://asciinema.org/a/219455.svg)](https://asciinema.org/a/219455)

## [fastlane](https://github.com/fastlane-queue/fastlane) service

[fastlane](https://github.com/fastlane-queue/fastlane) is a [redis](https://redis.io/)-based queueing service that outsmarts everyone else by using containers.

More seriously, though, [fastlane](https://github.com/fastlane-queue/fastlane) allows you to easily implement new workers in the form of containers.

Instead of the tedious, repetitive work of yesteryear where you had to implement a worker in language X or Y, you just spin a new container with all the dependencies you require already previously installed, and instruct [fastlane](https://github.com/fastlane-queue/fastlane) to run a command in that container. Bang! Instant Super-Powered Workers!

## Features

-   [x]  [Ad-Hoc execution of jobs (run job right now)](tests/func/test_adhoc.py#L11)
-   [x]  [Scheduled execution of jobs (run job next sunday at 6am, or run in 10 minutes from now)](tests/func/test_scheduled.py#L13);
-   [x]  [Crontab execution of jobs (run job at `*/10 * * * *` - every ten minutes)](tests/func/test_cron.py#L11);
-   [x]  [Allows job details to be updated](tests/func/test_update_details.py#L13);
-   [x]  [API to retrieve tasks, `/tasks`](tests/func/test_get_tasks.py#L11);
-   [x]  API to retrieve task details, `/tasks/my-task` (`<taskUrl>`);
-   [x]  API to retrieve job details, `<taskUrl>/jobs/<jobId>` (`<jobUrl>`);
-   [x]  API to stop running job (`<jobUrl>/stop`);
-   [x]  API to retry job (`<jobUrl>/retry`);
-   [x]  API to get logs(`<jobUrl>/logs`), stdout (`<jobUrl>/stdout`) and stderr (`<jobUrl>/stderr`) for last execution in jobs;
-   [x]  Job log output streaming using WebSockets (`ws://<jobUrl>/ws`) and `<jobUrl>/stream`;
-   [x]  API to retrieve execution details, `<jobUrl>/executions/<executionId>` (`<executionUrl>`);
-   [x]  API to stop execution, `<executionUrl>/stop`;
-   [x]  API to get logs(`<executionUrl>/stdout`), stdout (`<executionUrl>/stdout`) and stderr (`<executionUrl>/stderr`) for execution;
-   [x]  Job execution log output streaming using WebSockets (`ws://<executionUrl>/ws`) and `<executionUrl>/stream`;
-   [x]  Additional Job Metadata (useful for webhooks);
-   [x]  Configurable retries per job;
-   [x]  Configurable exponential back-off for retries and failures in monitoring of jobs;
-   [x]  Configurable hard timeout for each execution;
-   [x]  E-mail subscription to tasks;
-   [x]  Healthcheck of the MongoDB and Redis Connections;
-   [ ]  Web hooks on job start;
-   [x]  Web hooks on job completion;
-   [x]  Redact any env that contains blacklisted keywords;
-   [ ]  Exponential back-off parameters per job;
-   [x]  Self-healing handling of interrupted jobs;
-   [ ]  Self-healing handling of unscheduled periodical jobs;
-   [x]  Workers should handle SIGTERM and exit gracefully;
-   [x]  [Docker](https://docs.docker.com/) Container Runner (with [docker](https://docs.docker.com/) host pool);
-   [x]  [Docker](https://docs.docker.com/) Pool per task name (Regular Expressions);
-   [x]  Rename [docker](https://docs.docker.com/) containers after processing their details;
-   [x]  Command to prune processed containers;
-   [x]  Routes to remove/put back [docker](https://docs.docker.com/) host in job balancing;
-   [ ]  [Docker](https://docs.docker.com/) SSL connections;
-   [ ]  Circuit breaking when [docker](https://docs.docker.com/) host is unavailable;
-   [x]  Container Environment Variables per Job;
-   [x]  Configurable global limit for number of running jobs per task name (Regular Expressions);
-   [ ]  Limit of concurrent job executions per task;
-   [ ]  Kubernetes Container Runner;
-   [x]  [MongoDB](https://www.mongodb.com/) Task and Job Storage;
-   [x]  Structured Logging;
-   [x]  Monitoring of job completion;
-   [x]  Job Expiration;
-   [x]  Status Page with details on the farm status (executors, scheduled tasks and queue sizes);
-   [x]  Error handling mechanism (Sentry built-in, extensible)
-   [ ]  Per-job Error handling mechanism (Sentry built-in, extensible)
-   [ ]  Usage metrics (extensible);
-   [x]  Support [Redis](https://redis.io/) and [Redis](https://redis.io/) Sentinel;
-   [ ]  Support [Redis](https://redis.io/) Cluster;
-   [ ]  Comprehensive test coverage;
-   [x]  CORS headers in every API request (configurable);
-   [x]  Basic Auth support;
-   [x]  gzip all JSON responses for the API (for requests that accept gzip);
-   [x]  Store IP address of enqueued job for auditing (`X-Real-IP`, then `X-Forwarded-For`, then `request.addr`);
-   [ ]  Admin to inspect tasks and jobs.

## Getting started

Getting [fastlane](https://github.com/fastlane-queue/fastlane) up and running is very simple if you have both [docker](https://docs.docker.com/) and [docker-compose](https://docs.docker.com/compose/) installed.

We'll use a sample docker compose that gets all our requirements up (ps: this [docker-compose](https://docs.docker.com/compose/) file runs [Docker In Docker](https://hub.docker.com/_/docker/) and requires privileged mode to run):

```bash
$ curl https://raw.githubusercontent.com/fastlane-queue/fastlane/master/docker-compose-sample.yml | docker-compose -f - up -d

Starting fastlane...
Creating fastlane_mongo_1       ... done
Creating fastlane_docker-host_1 ... done
Creating fastlane_redis_1       ... done
Creating fastlane_fastlane_1    ... done
fastlane started successfully.
```

After that you can start using [fastlane](https://github.com/fastlane-queue/fastlane). For more details on getting started, read the [following page](https://fastlane.readthedocs.io/en/latest/getting-started/).

## Documentation

Read more about fastlane at [read the docs](https://fastlane.readthedocs.io/en/latest/).

## Contributing

Logo was created by [Artur Sousa](https://github.com/arturfsousa).

## License

Fastlane is licensed under the [MIT license](LICENSE).
