from derpconf.config import Config

Config.allow_environment_variables()

Config.define('ENV', 'development', 'Environment application is running in',
              'General')
Config.define('SECRET_KEY',
              'OTNDN0VCRDAtRTMyMS00NUM0LUFFQUYtNEI4QUE4RkFCRjUzCg==',
              'Secret key to use in flask.', 'General')

Config.define('REDIS_URL', 'redis://localhost:10100/0',
              'Redis connection string', 'Redis')

Config.define('EXECUTOR', 'easyq.worker.docker_executor',
              'Module full name where to find the Executor class', 'Worker')

Config.define(
    'MONGODB_SETTINGS', {
        'host': 'localhost',
        'port': 10101,
        'db': 'easyq',
        'serverSelectionTimeoutMS': 100,
        'connect': False,
    }, 'MongoDB socket timeout in ms', 'Models')
