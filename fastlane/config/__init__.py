# 3rd Party
from derpconf.config import Config

Config.allow_environment_variables()

Config.define(
    "DEBUG",
    False,
    "This configuration details if fastlane is running in debug mode.",
    "General",
)
Config.define(
    "ENV",
    "production",
    "This configuration details the environment fastlane is running in.",
    "General",
)
Config.define(
    "SECRET_KEY",
    "OTNDN0VCRDAtRTMyMS00NUM0LUFFQUYtNEI4QUE4RkFCRjUzCg==",
    """This configuration specifies the `SECRET_KEY` for Fastlane API.
This should be unique per environment.""",
    "General",
)

Config.define(
    "ENABLE_CORS",
    True,
    "This configuration enabled CORS headers in the API. CORS is enabled "
    "on '*' by default in Fastlane. It's the administrator's job to secure"
    " it behind some gateway.",
    "General",
)

Config.define(
    "CORS_ORIGINS",
    "*",
    "This configuration enabled CORS headers in the API.",
    "General",
)

Config.define(
    "REDIS_URL",
    "redis://localhost:10100/0",
    """Redis connection string in the form of 'redis://' protocol.

If `redis+sentinel` is used as protocol, instead, fastlane will
connect to sentinel to get redis host.""",
    "Redis",
)

Config.define(
    "WORKER_SLEEP_TIME_MS",
    1000,
    "Number of milliseconds that fastlane must sleep before getting the next job",
    "Worker",
)

Config.define(
    "HARD_EXECUTION_TIMEOUT_SECONDS",
    30 * 60,
    "Number of seconds that fastlane must wait before killing an execution",
    "Worker",
)

Config.define(
    "EXPONENTIAL_BACKOFF_MIN_MS",
    1000,
    "Number of milliseconds that fastlane must wait before the first retry in each job",
    "Worker",
)

Config.define(
    "EXPONENTIAL_BACKOFF_FACTOR",
    2,
    "Factor to multiply backoff by in each retry",
    "Worker",
)

Config.define(
    "WEBHOOKS_EXPONENTIAL_BACKOFF_MIN_MS",
    5000,
    "Number of milliseconds that fastlane must wait before "
    "the first retry in each webhook dispatch",
    "Worker",
)

Config.define(
    "WEBHOOKS_EXPONENTIAL_BACKOFF_FACTOR",
    2,
    "Factor to multiply backoff by in each retry for webhook dispatch",
    "Worker",
)

Config.define(
    "EXECUTOR",
    "fastlane.worker.docker_executor",
    "Module full name where to find the Executor class",
    "Worker",
)

Config.define(
    "DOCKER_HOSTS",
    [{"match": "", "hosts": ["localhost:2375"], "maxRunning": 2}],
    """Docker cluster definitions.
The `match` portion of each host definition specifies
a regular expression that must be match in order for the
job to execute in one of the docker hosts in the `hosts` key.
The `maxRunning` portion, specifies the maximum number of
concurrent jobs in this cluster.
If the regex is empty ("") it means that it matches anything.
The empty regex cluster definition should be the last one, otherwise
it will work all jobs.
""",
    "Docker Executor",
)

Config.define(
    "DOCKER_CIRCUIT_BREAKER_MAX_FAILS",
    5,
    "Maximum number of failures to docker host to stop sending new jobs",
    "Docker Executor",
)

Config.define(
    "DOCKER_CIRCUIT_BREAKER_RESET_TIMEOUT_SECONDS",
    60,
    "Number of seconds to reopen circuit and start sending new jobs to a docker host",
    "Docker Executor",
)

Config.define(
    "MONGODB_CONFIG",
    {
        "host": "mongodb://localhost:10101/fastlane",
        "db": "fastlane",
        "serverSelectionTimeoutMS": 100,
        "connect": False,
    },
    "MongoDB connection details.",
    "Models",
)

Config.define(
    "ERROR_HANDLERS",
    ["fastlane.errors.sentry.SentryErrorHandler"],
    "List of configured error handlers",
    "Errors",
)

Config.define("SENTRY_DSN", "", "Sentry DSN to send errors to", "Errors")

Config.define(
    "ENV_BLACKLISTED_WORDS",
    "password,key,secret,client_id",
    "Words that if present in environment variables are redacted",
    "API",
)

Config.define(
    "SMTP_USE_SSL",
    False,
    "Wheter the SMTP server used to send notifications uses SSL",
    "Email",
)

Config.define(
    "SMTP_HOST", None, "Host of the SMTP server used to send notifications", "Email"
)

Config.define(
    "SMTP_PORT", None, "Port of the SMTP server used to send notifications", "Email"
)

Config.define(
    "SMTP_USER", None, "User of the SMTP server used to send notifications", "Email"
)

Config.define(
    "SMTP_PASSWORD",
    None,
    "Password of the SMTP server used to send notifications",
    "Email",
)

Config.define(
    "SMTP_FROM",
    None,
    "From E-mail of the SMTP server used to send notifications",
    "Email",
)

Config.define(
    "PAGINATION_PER_PAGE",
    10,
    "Total items per page to be used on api pagination methods",
    "API",
)
