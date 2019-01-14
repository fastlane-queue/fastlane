# Job payload

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

-   `image` - This parameter specifies the [docker](https://docs.docker.com/) image that should be used to run this job;
-   `command` - The command that will be run by the job;
-   `envs` - The environment variables that will be set in the container when the job is run;
-   `startIn`, `startAt` and `cron` - Different ways to schedule the job. If none of these is passed, the job starts immediately. `startIn` gets a string with how much time in the future to start the job in the form of `2h30m50s`. `startAt` takes an UNIX UTC timestamp that will be used to determine when the job should start. `cron` takes a [cron format](https://en.wikipedia.org/wiki/Cron) string that determines how often this job should be executed;
-   `metadata` - This parameter is a dictionary that will be attached to the job's metadata as a `custom` key and can be used to store values that can be later on used by webhooks, as an example;
-   `notify` - This parameter specifies cases where the owner of the job wants to be notified by e-mail. This parameter is a dictionary with the `succeeds`, `fails` and `finishes` array keys. In the scenario above, when each job execution succeeds (exit code == 0), `success@mycompany.com` will receive an e-mail with the execution details. When each job execution fails (exit code != 0), `failure@mycompany.com` and `other@mycompany.com` both will receive an e-mail with the execution details. `whatever@mycompany.com` will receive e-mails with the execution details, for all executions of this job, independent of exit code;
-   `webhooks` - This parameter specifies cases where the owner of the job wants to dispatch webhooks with the execution details. This parameter is a dictionary with the `succeeds`, `fails` and `finishes` array keys. In the scenario above, when each job execution succeeds (exit code == 0), a `POST` request will be made against `http://my.website.com/rout` with the execution data as `JSON`. `fails` and `finishes` are analogous to the notify option. Only the `url` parameter is required;
-   `retries` - This argument determines whether this job should be retried (>0) and how many times. If this argument is not present in the body, retry is disabled;
-   `expiration` - If this argument is present, this determines a point in time where this job should not run anymore. It is an UNIX UTC timestamp. The purpose of this argument is for scenarios of high queueing, so the job can sit in the queue for a long time. In this scenario, after a long time, this job might not make sense anymore (i.e.: a push notification);
-   `timeout` - This is a timeout in seconds after which the job will be terminated. There's a hard limit in [fastlane](https://github.com/fastlane) and it will use whatever value is lower.

