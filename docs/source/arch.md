# Architecture and Design

## An example situation

We'll start with an example situation that we can explore in order to understand more about [fastlane](https://github.com/fastlane).

Let's say I want to run a job that sends an e-mail when something happens and I have a container already configured with templates and all I need to pass is the SMTP as an env variable and a command to execute a python script:

    $ curl -XPOST --header "Content-Type: application/json" -d'{"image": "my.docker.repo.com/my-send-email-image:latest", "command": "python /app/sendmail.py", "envs": {"SMTP_SERVER":"my-smtp-server"}}' http://fastlane.local:10000/tasks/send-very-specific-email
    {
        "taskId": "send-very-specific-email",
        "jobId": "5b8db248edc7d584132a6d4d",
        "queueJobId": "77cfabbb-1864-4073-afe7-0efe01014754"
    }

In this request I'm creating/updating a task called `send-very-specific-email` and creating a new job in it to execute the command `python /app/sendmail.py`. I hope you now have a **boatload** of questions, like:

-   Where did you get `/app/sendmail.py` from?
-   What version of the python interpreter are you running? Are you even sure python is installed?
-   What about the python and system libraries that `sendmail.py` depends on? When were they installed?
-   What is that jobId in the return of the `POST` and how do I use that?
-   What does it mean for that job to be in a queue? I thought you said that Ad-Hoc execution meant running the job **right now**!

We'll address these now.

## Design Decisions

[fastlane](https://github.com/fastlane) is by design a system with no authentication and authorization.

Users are responsible for specifying a task id that's globally unique. If two users specify a task with id 'run', their jobs will be grouped together (not an issue for [fastlane](https://github.com/fastlane), since every job has a globally unique id anyways). This might be confusing, though.

The decision here is to sacrifice isolation for simplicity. Usually a queueing system is a backend application, meaning that it's easy enough to construct a front-end for [fastlane](https://github.com/fastlane) that provides authentication and authorization to post jobs in tasks.

## The Container

As said previously, [fastlane](https://github.com/fastlane) uses containers to enable users to have very flexible workers. 

This means that the container must be created and published before creating a new job. And that's the beauty of the system. Never worry about versions of libraries that the worker has to deal with again.

Just pre-install everything you need in the container image, including the application you are running every job cycle, and publish that image to a container repository.

[fastlane](https://github.com/fastlane) supports versioning of containers. You can run the latest version, or just specify a tag to run (`stable` or `0.1.3` for instance).

And that's where `/app/sendmail.py` comes from. It was pre-installed in the container when it was published to the `my.docker.repo.com` container repository.

That also answers the second and third questions. All the dependencies get pre-installed within the container image.

## Tasks, Jobs and Executions in [fastlane](https://github.com/fastlane)

There are three levels in [fastlane](https://github.com/fastlane) hierarchy: tasks, jobs and executions.

Users group their units of work in tasks. Examples of tasks would be "system1-send-mail" or "system2-process-user-registration".

The name of the task is arbitrary and it's not enforced to be unique. It's advised to use a task name that includes your system name as to ensure uniqueness.

Jobs are created every time a task is enqueued. A job indicates whether it's scheduled and is basically a container for all the executions inside it.

A Job Execution is the actual unit of work. An execution has an image, a command and any other metadata that is required to run the unit of work.

Why aren't these details in the Job, instead of the execution? Because we can have many executions for a single job: Cron and retries are good examples of this behavior.

## Jobs Lifecycle

TBW.

