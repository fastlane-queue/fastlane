# Configuration Options

To generate a sample configuration file like this one: \`fastlane config\`.

```python
################################### General ####################################

## This configuration details the environment fastlane is running in.
## Defaults to: 'production'
#ENV = 'production'

## This configuration specifies the `SECRET_KEY` for Fastlane API. This should be
## unique per environment.
## Defaults to: 'OTNDN0VCRDAtRTMyMS00NUM0LUFFQUYtNEI4QUE4RkFCRjUzCg=='
#SECRET_KEY = 'OTNDN0VCRDAtRTMyMS00NUM0LUFFQUYtNEI4QUE4RkFCRjUzCg=='

################################################################################


##################################### Redis #####################################

## Redis connection string in the form of 'redis://' protocol.  If
## `redis+sentinel` is used as protocol, instead, fastlane will connect to
## sentinel to get redis host.
## Defaults to: 'redis://localhost:10100/0'
#REDIS_URL = 'redis://localhost:10100/0'

################################################################################


#################################### Worker ####################################

## Number of milliseconds that fastlane must sleep before getting the next job
## Defaults to: 10
#WORKER_SLEEP_TIME_MS = 10

## Number of seconds that fastlane must wait before killing an execution
## Defaults to: 1800
#HARD_EXECUTION_TIMEOUT_SECONDS = 1800

## Number of milliseconds that fastlane must wait before the first retry in each
## job
## Defaults to: 1000
#EXPONENTIAL_BACKOFF_MIN_MS = 1000

## Factor to multiply backoff by in each retry
## Defaults to: 2
#EXPONENTIAL_BACKOFF_FACTOR = 2

## Number of milliseconds that fastlane must wait before the first retry in each
## webhook dispatch
## Defaults to: 5000
#WEBHOOKS_EXPONENTIAL_BACKOFF_MIN_MS = 5000

## Factor to multiply backoff by in each retry for webhook dispatch
## Defaults to: 2
#WEBHOOKS_EXPONENTIAL_BACKOFF_FACTOR = 2

## Module full name where to find the Executor class
## Defaults to: 'fastlane.worker.docker_executor'
#EXECUTOR = 'fastlane.worker.docker_executor'

################################################################################


############################### Docker Executor ################################

## Docker cluster definitions. The `match` portion of each host definition
## specifies a regular expression that must be match in order for the job to
## execute in one of the docker hosts in the `hosts` key. The `maxRunning`
## portion, specifies the maximum number of concurrent jobs in this cluster.
## If the regex is empty ("") it means that it matches anything. The empty
## regex cluster definition should be the last one, otherwise it will work all
## jobs.
## Defaults to: [
#    {'match': '', 'hosts': ['localhost:2375'], 'maxRunning': 2},
#]

#DOCKER_HOSTS = [
#    {'match': '', 'hosts': ['localhost:2375'], 'maxRunning': 2},
#]


## Maximum number of failures to docker host to stop sending new jobs
## Defaults to: 5
#DOCKER_CIRCUIT_BREAKER_MAX_FAILS = 5

## Number of seconds to reopen circuit and start sending new jobs to a docker
## host
## Defaults to: 60
#DOCKER_CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS = 60

################################################################################


#################################### Models ####################################

## MongoDB connection details.
## Defaults to: {'host': 'mongodb://localhost:10101/fastlane', 'db': 'fastlane', 'serverSelectionTimeoutMS': 100, 'connect': False}
#MONGODB_CONFIG = {'host': 'mongodb://localhost:10101/fastlane', 'db': 'fastlane', 'serverSelectionTimeoutMS': 100, 'connect': False}

################################################################################


#################################### Errors ####################################

## List of configured error handlers
## Defaults to: [
#    'fastlane.errors.sentry.SentryErrorHandler',
#]

#ERROR_HANDLERS = [
#    'fastlane.errors.sentry.SentryErrorHandler',
#]


## Sentry DSN to send errors to
## Defaults to: ''
#SENTRY_DSN = ''

################################################################################


##################################### API ######################################

## Words that if present in environment variables are redacted
## Defaults to: 'password,key,secret,client_id'
#ENV_BLACKLISTED_WORDS = 'password,key,secret,client_id'

## Total items per page to be used on api pagination methods
## Defaults to: 10
#PAGINATION_PER_PAGE = 10

################################################################################


##################################### Email #####################################

## Wheter the SMTP server used to send notifications uses SSL
## Defaults to: False
#SMTP_USE_SSL = False

## Host of the SMTP server used to send notifications
## Defaults to: None
#SMTP_HOST = None

## Port of the SMTP server used to send notifications
## Defaults to: None
#SMTP_PORT = None

## User of the SMTP server used to send notifications
## Defaults to: None
#SMTP_USER = None

## Password of the SMTP server used to send notifications
## Defaults to: None
#SMTP_PASSWORD = None

## From E-mail of the SMTP server used to send notifications
## Defaults to: None
#SMTP_FROM = None

################################################################################


```
