import fakeredis
from flask import Flask
from flask_redis import FlaskRedis

import easyq.api.rqb as rqb
from easyq.api.enqueue import bp as enqueue
from easyq.api.healthcheck import bp as healthcheck


class Application:
    def __init__(self, config, testing=False):
        self.config = config
        self.create_app(testing)

    def create_app(self, testing):
        self.app = Flask('easyq')
        self.app.testing = testing
        self.app.config.update(self.config.items)
        self.connect_redis()
        self.connect_queue()

        self.app.register_blueprint(healthcheck)
        self.app.register_blueprint(enqueue)

    def connect_redis(self):
        if self.app.testing:
            self.app.redis = FlaskRedis.from_custom_provider(
                fakeredis.FakeStrictRedis)
            self.app.redis.connect = self._mock_redis(True)
            self.app.redis.disconnect = self._mock_redis(False)
        else:
            self.app.redis = FlaskRedis()

        self.app.redis.init_app(self.app)

    def connect_queue(self):
        self.app.queue = None
        self.app.register_blueprint(rqb.bp)
        rqb.init_app(self.app)

    def run(self, host, port):
        self.app.run(host, port)

    def _mock_redis(self, connected):
        def handle():
            self.app.redis._redis_client.connected = connected

        return handle
