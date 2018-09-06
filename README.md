# easyq

EasyQ is a redis-based queueing service that outsmarts everyone else by using containers.

More seriously, though, EasyQ allows you to easily implement new workers in the form of containers.

Instead of the tedious, repetitive work of yesteryear where you had to implement a worker in language X or Y, you just spin a new container with all the dependencies you require already previously installed, and instruct EasyQ to run a command in that container. Bang! Instant Super-Powered Workers!

Aside from freedom, EasyQ also provides:

* Ad-Hoc execution of jobs (run job right now);
* Scheduled execution of jobs (run job next sunday at 6am, or run in 10 minutes from now);
* Crontab execution of jobs (run job at "*/10 * * * *" - every ten minutes);
* Docker Container Runner;
* Kubernetes Container Runner;
* MongoDB Task and Job Storage;
* Structured Logging;
* Monitoring of job completion;
* Configurable retries per job;
* Configurable global and task-scoped limits for number of running jobs;
* API to retrieve job and task details;
* Admin to inspect tasks and jobs;
* Admin to inspect health of queueing system (error queue, size of queues, etc).

EasyQ is by design a system with no authentication and authorization.

Users are responsible for specifying a task id that's globally unique. If two users specify a task with id 'run', their jobs will be grouped together (not an issue for EasyQ, since every job has a globally unique id anyways). This might be confusing, though.

The decision here is to sacrifice isolation for simplicity. Usually a queueing system is a backend application, meaning that it's easy enough to construct a front-end for EasyQ that provides authentication and authorization to post jobs in tasks.

## Let's create a new job and fire it!

Let's say I want to run a job that sends an e-mail when something happens and I have a container already configured with templates and all I need to pass is the SMTP as an env variable and a command to execute a python script:

```
$ curl -XPOST -d'{"image": "my.docker.repo.com/my-image:latest", "command": "python /app/my-script.py", "envs": {"SMTP_SERVER":"my-smtp-server"}}' http://easyq.local:10000/tasks/send-very-specific-email
{
    "taskId": "sou-o-jeff",
    "jobId": "5b8db248edc7d584132a6d4d",
    "queueJobId": "77cfabbb-1864-4073-afe7-0efe01014754",
    "status": "queued"
}
```

In this request I'm creating/updating a task called `send-very-specific-email` and creating a new job in it to execute the command `python /app/my-script.py`. I hope you now have a **boatload** of questions, like:

* Where did you get `/app/my-script.py` from?
* What version of the python interpreter are you running? Are you even sure python is installed?
* What about the python and system libraries that `my-script.py` depends on? When were they installed?
* What is that jobId in the return of the `POST` and how do I use that?
* What does it mean for that job to be `queued`? I thought you said that Ad-Hoc execution meant running the job **right now**!

Those are all very good questions! Let's discuss each one of those.


## The Container

As said previously, EasyQ uses containers to enable users to have very flexible workers. 

This means that the container must be created and published before creating a new job. And that's the beauty of the system. Never worry about versions of libraries that the worker has to deal with again.

Just pre-install everything you need in the container image, including the application you are running every job cycle, and publish that image to a container repository.

EasyQ supports versioning of containers. You can run the latest version, or just specify a tag to run (`stable` or `0.1.3` for instance).

And that's where `/app/my-script.py` comes from. It was pre-installed in the container when it was published to the `my.docker.repo.com` container repository.

That also answers the second and third questions. All the dependencies get pre-installed with the container.

## Tasks and Jobs in EasyQ

TBW.

## Jobs Lifecycle

TBW.

## Jobs Options

TBW.

## API

TBW.

## EasyQ Workers

TBW.
