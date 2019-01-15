![](fastlane-logo.svg)

[![](https://img.shields.io/badge/github-repo-blue.svg)](https://github.com/heynemann/fastlane) [![](https://travis-ci.org/heynemann/fastlane.svg?branch=master)](https://travis-ci.org/heynemann/fastlane)[![](https://readthedocs.org/projects/fastlane/badge/?version=latest)](https://fastlane.readthedocs.io/en/latest/?badge=latest) [![](https://api.codacy.com/project/badge/Grade/55791f14727846f5a330f409ff4266c1)](https://www.codacy.com/app/heynemann/fastlane?utm_source=github.com&utm_medium=referral&utm_content=heynemann/fastlane&utm_campaign=Badge_Grade) [![](https://bettercodehub.com/edge/badge/heynemann/fastlane?branch=master)](https://bettercodehub.com/results/heynemann/fastlane) [![](https://img.shields.io/github/issues/heynemann/fastlane.svg)](https://github.com/heynemann/fastlane/issues) [![](https://img.shields.io/github/followers/espadrine.svg?label=Follow&style=social)](https://github.com/heynemann/fastlane)

[![](https://asciinema.org/a/219455.svg)](https://asciinema.org/a/219455)

# Why [fastlane](https://github.com/heynemann/fastlane)?

[fastlane](https://github.com/heynemann/fastlane) is a [redis](https://redis.io/)-based queueing service that outsmarts everyone else by using containers.

More seriously, though, [fastlane](https://github.com/heynemann/fastlane) allows you to easily implement new workers in the form of containers.

Instead of the tedious, repetitive work of yesteryear where you had to implement a worker in language X or Y, you just spin a new container with all the dependencies you require already previously installed, and instruct [fastlane](https://github.com/heynemann/fastlane) to run a command in that container. Bang! Instant Super-Powered Workers!

# Features

-   [x]  Ad-Hoc execution of jobs (run job right now);
-   [x]  Scheduled execution of jobs (run job next sunday at 6am, or run in 10 minutes from now);
-   [x]  Crontab execution of jobs (run job at `_/10 _ \* \* \*` - every ten minutes);
-   [x]  API to retrieve tasks, `/tasks`;
-   [x]  API to retrieve task details, `/tasks/my-task` (`<taskUrl>`);
-   [x]  API to retrieve job details, `<taskUrl>/jobs/<jobId>` (`<jobUrl>`);
-   [x]  API to stop running job (`<jobUrl>/stop`);
-   [x]  API to retry job (`<jobUrl>/retry`);
-   [x]  API to get stdout (`<jobUrl>/stdout`) and stderr (`<jobUrl>/stderr`) for last execution in jobs;
-   [x]  Job log output streaming using WebSockets (`ws://<jobUrl>/ws`) and `<jobUrl>/stream`;
-   [x]  Additional Job Metadata (useful for webhooks);
-   [x]  Configurable retries per job;
-   [x]  Configurable exponential back-off for retries and failures in monitoring of jobs;
-   [x]  Configurable hard timeout for each execution;
-   [x]  E-mail subscription to tasks;
-   [x]  Web hooks on job completion;
-   [x]  Redact any env that contains blacklisted keywords;
-   [ ]  Exponential back-off parameters per job;
-   [ ]  Self-healing handling of interrupted jobs;
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
-   [x]  gzip all JSON responses for the API (for requests that accept gzip);
-   [ ]  Admin to inspect tasks and jobs.

## License

fastlane is [MIT licensed](https://opensource.org/licenses/MIT).

## Contributions

Logo was created by [Artur Sousa](https://github.com/arturfsousa).
