from derpconf.config import Config

Config.allow_environment_variables()

Config.define('REDIS_HOST', 'localhost', 'Host to connect to redis', 'Redis')
Config.define('REDIS_PORT', 10100, 'Port to connect to redis', 'Redis')
