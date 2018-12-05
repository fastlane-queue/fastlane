from derpconf.config import Config

Config.allow_environment_variables()

Config.define("ENV", "development", "Environment application is running in", "General")
Config.define(
    "SECRET_KEY",
    "OTNDN0VCRDAtRTMyMS00NUM0LUFFQUYtNEI4QUE4RkFCRjUzCg==",
    "Secret key to use in flask.",
    "General",
)

Config.define(
    "REDIS_URL", "redis://localhost:10100/0", "Redis connection string", "Redis"
)

Config.define(
    "WORKER_SLEEP_TIME_MS",
    10,
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
    "EXECUTOR",
    "fastlane.worker.docker_executor",
    "Module full name where to find the Executor class",
    "Worker",
)

Config.define(
    "DOCKER_HOSTS",
    '[{"match": "", "hosts": ["localhost:2376"], "maxRunning":2}]',
    "Docker Hosts to add to pool",
    "Docker Executor",
)

Config.define(
    "MONGODB_CONFIG",
    """{
        "host": "localhost",
        "port": 10101,
        "db": "fastlane",
        "serverSelectionTimeoutMS": 100,
        "connect": false
    }""",
    "MongoDB configuration",
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
    "Errors",
)
