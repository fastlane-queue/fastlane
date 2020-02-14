# Standard Library
from json import dumps
from random import randrange
from uuid import uuid4

# 3rd Party
from preggy import expect

# Fastlane
from fastlane.worker.docker import BLACKLIST_KEY


def test_docker_blacklist1(client):
    """Test blacklisting a docker server"""

    def ensure_blacklist(method):
        docker_host = "{domain}:{port}".format(
            domain=str(uuid4()).replace("-", "."),
            port=int(randrange(10, 99999))  # nosec
        )

        data = {"host": docker_host}
        response = getattr(client, method)(
            "/docker-executor/blacklist", data=dumps(data), follow_redirects=True
        )

        expect(response.status_code).to_equal(200)
        expect(response.data).to_be_empty()

        app = client.application

        res = app.redis.exists(BLACKLIST_KEY)
        expect(res).to_be_true()

        res = app.redis.sismember(BLACKLIST_KEY, docker_host)
        expect(res).to_be_true()

    for method in ["post", "put"]:
        ensure_blacklist(method)


def test_docker_blacklist2(client):
    """
    Test blacklisting a docker server with invalid body or
    without a host property in the JSON body
    """

    def ensure_blacklist(method):
        response = getattr(client, method)(
            "/docker-executor/blacklist", data=dumps({}), follow_redirects=True
        )

        expect(response.status_code).to_equal(400)
        expect(response.data).to_be_like(
            "Failed to add host to blacklist because 'host' attribute was not found in JSON body."
        )

        app = client.application

        res = app.redis.exists(BLACKLIST_KEY)
        expect(res).to_be_false()

    for method in ["post", "put"]:
        ensure_blacklist(method)


def test_docker_blacklist3(client):
    """Test removing from blacklist a docker server"""
    docker_host = "{domain}:{port}".format(
        domain=str(uuid4()).replace("-", "."),
        port=int(randrange(10, 99999))  # nosec
    )

    data = {"host": docker_host}
    response = client.post(
        "/docker-executor/blacklist", data=dumps(data), follow_redirects=True
    )

    expect(response.status_code).to_equal(200)
    expect(response.data).to_be_empty()

    app = client.application

    res = app.redis.exists(BLACKLIST_KEY)
    expect(res).to_be_true()

    res = app.redis.sismember(BLACKLIST_KEY, docker_host)
    expect(res).to_be_true()

    data = {"host": docker_host}
    response = client.delete(
        "/docker-executor/blacklist", data=dumps(data), follow_redirects=True
    )

    expect(response.status_code).to_equal(200)
    expect(response.data).to_be_empty()

    app = client.application

    res = app.redis.exists(BLACKLIST_KEY)
    expect(res).to_be_false()


def test_docker_blacklist4(client):
    """
    Test removing a server from blacklist with invalid body or
    without a host property in the JSON body
    """

    response = client.delete(
        "/docker-executor/blacklist", data=dumps({}), follow_redirects=True
    )

    expect(response.status_code).to_equal(400)
    expect(response.data).to_be_like(
        "Failed to remove host from blacklist because 'host' attribute was not found in JSON body."
    )
