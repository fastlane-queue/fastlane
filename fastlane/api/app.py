# Standard Library
import logging
import sys
from json import loads

# 3rd Party
import rq_dashboard
import structlog
from flask import Flask
from flask_cors import CORS
from flask_redis import FlaskRedis
from flask_redis_sentinel import SentinelExtension
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from structlog.processors import (
    JSONRenderer,
    StackInfoRenderer,
    TimeStamper,
    format_exc_info,
)
from structlog.stdlib import add_log_level, add_logger_name, filter_by_level

# Fastlane
import fastlane.api.gzipped as gzipped
import fastlane.api.metrics as metrics
import fastlane.api.rqb as rqb
from fastlane.api.enqueue import bp as enqueue
from fastlane.api.execution import bp as execution_api
from fastlane.api.healthcheck import bp as healthcheck
from fastlane.api.status import bp as status
from fastlane.api.stream import bp as stream
from fastlane.api.task import bp as task_api
from fastlane.models import db


class Application:
    def __init__(self, config, log_level, testing=False, auto_connect_db=True):
        self.config = config
        self.logger = None
        self.log_level = log_level

        self.create_app(testing, auto_connect_db=auto_connect_db)

    def create_app(self, testing, auto_connect_db=True):
        self.app = Flask("fastlane")

        self.testing = testing
        self.app.testing = testing
        self.app.config.from_object(rq_dashboard.default_settings)
        self.app.error_handlers = []

        for key in self.config.items.keys():
            self.app.config[key] = self.config[key]

        self.app.config["ENV"] = self.config.ENV
        self.app.config["DEBUG"] = self.config.DEBUG
        self.app.original_config = self.config
        self.app.log_level = self.log_level
        self.configure_logging()
        self.connect_redis()
        self.connect_queue()

        if auto_connect_db:
            self.connect_db()
        self.load_executor()
        self.load_error_handlers()

        enable_cors = self.app.config["ENABLE_CORS"]

        if (
            isinstance(enable_cors, (str, bytes)) and enable_cors.lower() == "true"
        ) or (isinstance(enable_cors, (bool)) and enable_cors):
            self.app.logger.info(
                f'Configured CORS to allow access from \'{self.app.config["CORS_ORIGINS"]}\'.'
            )
            CORS(self.app)

        metrics.init_app(self.app)
        self.app.register_blueprint(metrics.bp)
        self.app.register_blueprint(healthcheck)
        self.app.register_blueprint(enqueue)
        self.app.register_blueprint(task_api)
        self.app.register_blueprint(execution_api)
        self.app.register_blueprint(status)

        self.app.register_blueprint(gzipped.bp)
        gzipped.init_app(self.app)

        sockets = Sockets(self.app)
        sockets.register_blueprint(stream)

    def configure_logging(self):
        if self.app.testing:
            structlog.reset_defaults()

        disabled = [
            "docker.utils.config",
            "docker.auth",
            "docker.api.build",
            "docker.api.swarm",
            "docker.api.image",
            "rq.worker",
            "werkzeug",
            "requests",
            "urllib3",
        ]

        for logger in disabled:
            log = logging.getLogger(logger)
            log.setLevel(logging.ERROR)
            log.disabled = True
        self.app.logger.disabled = True

        logging.basicConfig(
            level=self.log_level, stream=sys.stdout, format="%(message)s"
        )

        chain = [
            filter_by_level,
            add_log_level,
            add_logger_name,
            TimeStamper(fmt="iso"),
            StackInfoRenderer(),
            format_exc_info,
            JSONRenderer(indent=1, sort_keys=True),
        ]

        logger = logging.getLogger(__name__)

        if self.testing:
            chain = []
            logger = structlog.ReturnLogger()

        log = structlog.wrap_logger(
            logger,
            processors=chain,
            context_class=dict,
            wrapper_class=structlog.stdlib.BoundLogger,
            # cache_logger_on_first_use=True,
        )
        self.logger = log
        self.app.logger = self.logger

    def connect_redis(self):
        self.logger.debug("Connecting to redis...")

        if self.app.testing:
            self.logger.info("Configuring Fake Redis...")
            import fakeredis

            self.app.redis = FlaskRedis.from_custom_provider(fakeredis.FakeStrictRedis)
            self.app.redis.connect = self._mock_redis(True)
            self.app.redis.disconnect = self._mock_redis(False)
            self.app.redis.init_app(self.app)
        elif self.app.config["REDIS_URL"].startswith("redis+sentinel"):
            self.logger.info(
                "Configuring Redis Sentinel...", redis_url=self.app.config["REDIS_URL"]
            )
            redis_sentinel = SentinelExtension()
            redis_connection = redis_sentinel.default_connection
            redis_sentinel.init_app(self.app)
            self.app.redis = redis_connection
        else:
            self.logger.info(
                "Configuring Redis...", redis_url=self.app.config["REDIS_URL"]
            )
            self.app.redis = FlaskRedis()
            self.app.redis.init_app(self.app)

        self.logger.info("Connection to redis successful")

    def connect_queue(self):
        self.app.queue = None
        self.app.register_blueprint(rqb.bp)
        rqb.init_app(self.app)

    def connect_db(self):
        settings = self.app.config["MONGODB_CONFIG"]

        if isinstance(settings, (dict,)):
            self.app.config["MONGODB_SETTINGS"] = settings
        else:
            self.app.config["MONGODB_SETTINGS"] = loads(
                self.app.config["MONGODB_CONFIG"]
            )

        self.logger.info(
            "Connecting to MongoDB...", mongo=self.app.config["MONGODB_SETTINGS"]
        )
        db.init_app(self.app)
        self.logger.info(
            "Connected to MongoDB successfully.",
            mongo=self.app.config["MONGODB_SETTINGS"],
        )

    def load_executor(self):
        name = self.config.EXECUTOR
        parts = name.split(".")
        executor_module = __import__(".".join(parts), None, None, [parts[-1]], 0)

        self.app.executor_module = executor_module

        blueprint = getattr(executor_module, "bp", None)

        if blueprint is not None:
            self.app.register_blueprint(blueprint)

        self.app.executor = self.app.executor_module.Executor(self.app)

    def load_error_handlers(self):
        self.app.error_handlers = []

        for handler_name in self.app.config["ERROR_HANDLERS"]:
            parts = handler_name.split(".")
            obj = __import__(".".join(parts[:-1]), None, None, [parts[-1]], 0)
            obj = getattr(obj, parts[-1])

            self.app.error_handlers.append(obj(self.app))

        self.app.report_error = self.report_error

    def report_error(self, err, metadata=None):
        for handler in self.app.error_handlers:
            handler.report(err, metadata)

    def run(self, host, port):
        server = pywsgi.WSGIServer(
            (host, port), self.app, handler_class=WebSocketHandler
        )
        server.serve_forever()

    def _mock_redis(self, connected):
        def handle():
            self.app.redis._redis_client.connected = connected

        return handle
