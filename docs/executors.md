# Executors

Users can implement their own custom container executors. [fastlane](https://github.com/fastlane) comes bundled with the [docker](https://docs.docker.com/) executor.

## Docker Executor

The [docker](https://docs.docker.com/) executor features a pool of [docker](https://docs.docker.com/) hosts that execute commands for you.

### Pool Configuration

Configuring the pool is done with the `DOCKER_HOSTS` configuration. It is a list that specifies the logical farms of [docker](https://docs.docker.com/) hosts.

An example configuration with two pools:

```python
DOCKER_HOSTS = [
    {
        "match": "producta.+",
        "hosts": ["docker-host1.company.com", "docker-host2.company.com"],
        "maxRunning": 10
    },
    {
        "match": "productb.+",
        "hosts": ["docker-host5.company.com", "docker-host6.company.com"],
        "maxRunning": 10
    },
    {
        "match": "",
        "hosts": ["docker-host3.company.com", "docker-host4.company.com"],
        "maxRunning": 10
    },
]
```

This configuration ensures that any tasks whose id start with `producta` like `producta-send-notifications` end up in a farm with the `docker-host1.company.com` and `docker-host2.company.com` hosts. If, on the other hand, the task id starts with `productb` then the job will run in the farm with the `docker-host5.company.com` and `docker-host6.company.com` hosts. Any other task id's will be executed in the farm with the `docker-host3.company.com` and `docker-host4.company.com` hosts.

The `maxRunning` parameter indicates how many concurrent jobs can be run in the farm.

### [Docker](https://docs.docker.com/) Executor Blacklisting

In order to improve on reliability and at the same time allow for fast and safe upgrades of [docker](https://docs.docker.com/) hosts, [fastlane](https://github.com/fastlane) comes bundled with a route for blacklisting [docker](https://docs.docker.com/) hosts.

The use case for this blacklist is as follows:

-   `POST` to the <http://fastlane.local:10000/docker-executor/blacklist> with a body of `{"host": "docker-host1.company.com:1234"}`;
-   Now the blacklisted host will not receive any new jobs;
-   Wait for all the running jobs to finish;
-   Upgrade, change, do anything that needs to be done with the host and get it back online;
-   `DEL` to the <http://fastlane.local:10000/docker-executor/blacklist> with a body of `{"host": "docker-host1.company.com:1234"}`.

Then do the same for all the other hosts.

**WARNING**: Please ensure that at least one [docker](https://docs.docker.com/) host is available and **NOT** blacklisted in each farm. If all hosts are blacklisted, [fastlane](https://github.com/fastlane) will start dropping jobs on the affected farms.

## Custom Executor

TBW.
