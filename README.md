# easyq

EasyQ is a redis-based queueing service that outsmarts everyone else by using containers.

More seriously, though, EasyQ allows you to easily implement new workers in the form of containers.

Instead of the tedious, repetitive work of yesteryear where you had to implement a worker in language X or Y, you just spin a new container with all the dependencies you require already previously installed, and instruct EasyQ to run a command in that container. Bang! Instant Super-Powered Workers!

Aside from freedom, EasyQ also provides:

- [x] Ad-Hoc execution of jobs (run job right now);
- [x] Scheduled execution of jobs (run job next sunday at 6am, or run in 10 minutes from now);
- [x] Crontab execution of jobs (run job at "*/10 * * * *" - every ten minutes);
- [x] Configurable retries per job;
- [x] Configurable exponential back-off for retries and failures in monitoring of jobs;
- [x] Configurable hard timeout for each execution;
- [ ] Exponential back-off parameters per job;
- [ ] Self-healing handling of interrupted jobs;
- [ ] Job log output streaming using WebSockets;
- [x] Workers should handle SIGTERM and exit gracefully;
- [x] Docker Container Runner (with Docker Host Pool);
- [x] Docker Pool per task name (Regular Expressions);
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
- [ ] Admin to inspect tasks and jobs;
- [x] Admin to inspect health of queueing system (error queue, size of queues, etc).

EasyQ is by design a system with no authentication and authorization.

Users are responsible for specifying a task id that's globally unique. If two users specify a task with id 'run', their jobs will be grouped together (not an issue for EasyQ, since every job has a globally unique id anyways). This might be confusing, though.

The decision here is to sacrifice isolation for simplicity. Usually a queueing system is a backend application, meaning that it's easy enough to construct a front-end for EasyQ that provides authentication and authorization to post jobs in tasks.

## Let's create a new job and fire it!

Let's say I want to run a job that sends an e-mail when something happens and I have a container already configured with templates and all I need to pass is the SMTP as an env variable and a command to execute a python script:

```
$ curl -XPOST --header "Content-Type: application/json" -d'{"image": "my.docker.repo.com/my-send-email-image:latest", "command": "python /app/sendmail.py", "envs": {"SMTP_SERVER":"my-smtp-server"}}' http://easyq.local:10000/tasks/send-very-specific-email
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

Those are all very good questions! Let's discuss each one of those.


## The Container

As said previously, EasyQ uses containers to enable users to have very flexible workers. 

This means that the container must be created and published before creating a new job. And that's the beauty of the system. Never worry about versions of libraries that the worker has to deal with again.

Just pre-install everything you need in the container image, including the application you are running every job cycle, and publish that image to a container repository.

EasyQ supports versioning of containers. You can run the latest version, or just specify a tag to run (`stable` or `0.1.3` for instance).

And that's where `/app/sendmail.py` comes from. It was pre-installed in the container when it was published to the `my.docker.repo.com` container repository.

That also answers the second and third questions. All the dependencies get pre-installed within the container image.

## Tasks, Jobs and Executions in EasyQ

There are three levels in EasyQ hierarchy: tasks, jobs and executions.

Users group their units of work in tasks. Examples of tasks would be "system1-send-mail" or "system2-process-user-registration".

The name of the task is arbitrary and it's not enforced to be unique. It's advised to use a task name that includes your system name as to ensure uniqueness.

Jobs are created every time a task is enqueued. A job indicates whether it's scheduled and is basically a container for all the executions inside it.

A Job Execution is the actual unit of work. An execution has an image, a command and any other metadata that is required to run the unit of work.

Why aren't these details in the Job, instead of the execution? Because we can have many executions for a single job: Cron and retries are good examples of this behavior.

## Jobs Lifecycle

TBW.

## Jobs Options

TBW.

## API

TBW.

## EasyQ Workers

TBW.

## Configurations

TBW.

## Contributing

TBW.
