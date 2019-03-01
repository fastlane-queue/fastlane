# Standard Library
from json import loads
from unittest.mock import MagicMock

# 3rd Party
from preggy import expect

# Fastlane
from fastlane.models import db


def test_healthcheck1(client):
    """Test healthcheck works if redis is live"""

    response = client.get("/healthcheck", follow_redirects=True)
    expect(response.status_code).to_equal(200)

    obj = loads(response.data)
    expect(obj["redis"]).to_be_true()
    expect(obj["mongo"]).to_be_true()
    expect(obj["errors"]).to_be_empty()

    response = client.get("/", follow_redirects=True)
    expect(response.status_code).to_equal(200)

    obj = loads(response.data)
    expect(obj["redis"]).to_be_true()
    expect(obj["mongo"]).to_be_true()
    expect(obj["errors"]).to_be_empty()


def test_healthcheck2(client):
    """Test healthcheck works if redis is offline"""
    client.application.redis = MagicMock()
    client.application.redis.ping.return_value = False

    response = client.get("/healthcheck", follow_redirects=True)
    expect(response.status_code).to_equal(500)

    obj = loads(response.data)
    expect(obj["redis"]).to_be_false()
    expect(obj["mongo"]).to_be_true()
    expect(obj["errors"]).to_length(1)

    err = obj["errors"][0]
    expect(err["message"]).to_equal(
        "Connection to redis failed (error: ping returned False)."
    )
    expect(err["source"]).to_equal("redis")


def test_healthcheck3(client):
    """Test healthcheck works if redis raises"""
    client.application.redis = MagicMock()
    client.application.redis.ping.side_effect = RuntimeError("test")

    response = client.get("/healthcheck", follow_redirects=True)
    expect(response.status_code).to_equal(500)

    obj = loads(response.data)
    expect(obj["redis"]).to_be_false()
    expect(obj["mongo"]).to_be_true()
    expect(obj["errors"]).to_length(1)

    err = obj["errors"][0]
    expect(err["message"]).to_equal("Connection to redis failed (error: test).")
    expect(err["source"]).to_equal("redis")


def test_healthcheck4(client):
    """Test healthcheck works if mongo is offline"""

    with client.application.app_context():
        find_mock = MagicMock()
        find_mock.side_effect = RuntimeError(
            "MongoMock is emulating a connection error."
        )
        # replacing properties is weird
        db._connection = MagicMock()
        db.connection.fastlane = MagicMock()
        db.connection.fastlane.jobs = MagicMock()
        db.connection.fastlane.jobs.find = find_mock

        response = client.get("/healthcheck", follow_redirects=True)
        expect(response.status_code).to_equal(500)

        obj = loads(response.data)
        expect(obj["redis"]).to_be_true()
        expect(obj["mongo"]).to_be_false()
        expect(obj["errors"]).to_length(1)

        err = obj["errors"][0]
        expect(err["message"]).to_equal("MongoMock is emulating a connection error.")
        expect(err["source"]).to_equal("mongo")
