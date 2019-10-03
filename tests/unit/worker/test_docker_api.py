# Standard Library
from json import dumps

# 3rd Party
from preggy import expect

# Fastlane
from fastlane.worker.docker.api import validate_hostname


def test_validate_hostname1():
    expect(validate_hostname("example.com")).to_be_false()


def test_validate_hostname2():
    expect(validate_hostname("example.com/")).to_be_false()


def test_validate_hostname3():
    expect(validate_hostname("example.com:abcd")).to_be_false()


def test_validate_hostname4():
    expect(validate_hostname("example.com:1234")).to_be_true()


def test_add_to_blacklist1(client):
    """Test adding to blacklist without payload returns 400"""
    with client.application.app_context():
        resp = client.post(
            f"/docker-executor/blacklist"
        )
        expect(resp.status_code).to_equal(400)


def test_add_to_blacklist2(client):
    """Test adding to blacklist without host on payload returns 400"""

    with client.application.app_context():
        resp = client.post(
            f"/docker-executor/blacklist",
            data=dumps({
                "myparam": "abc"
            })
        )
        expect(resp.status_code).to_equal(400)


def test_add_to_blacklist3(client):
    """Test adding to blacklist with valid host on payload returns 400"""

    with client.application.app_context():
        resp = client.post(
            f"/docker-executor/blacklist",
            data=dumps({
                "host": "example.com"
            })
        )
        expect(resp.status_code).to_equal(400)


def test_add_to_blacklist4(client):
    """Test adding to blacklist with valid host on payload returns 200"""

    with client.application.app_context():
        resp = client.post(
            f"/docker-executor/blacklist",
            data=dumps({
                "host": "example.com:1234"
            })
        )
        expect(resp.status_code).to_equal(200)


def test_remove_from_blacklist1(client):
    """Test adding to blacklist without payload returns 400"""
    with client.application.app_context():
        resp = client.delete(
            f"/docker-executor/blacklist"
        )
        expect(resp.status_code).to_equal(400)


def test_remove_from_blacklist2(client):
    """Test adding to blacklist without host on payload returns 400"""

    with client.application.app_context():
        resp = client.delete(
            f"/docker-executor/blacklist",
            data=dumps({
                "myparam": "abc"
            })
        )
        expect(resp.status_code).to_equal(400)


def test_remove_from_blacklist3(client):
    """Test adding to blacklist with valid host on payload returns 400"""

    with client.application.app_context():
        resp = client.delete(
            f"/docker-executor/blacklist",
            data=dumps({
                "host": "example.com"
            })
        )
        expect(resp.status_code).to_equal(400)


def test_remove_from_blacklist4(client):
    """Test adding to blacklist with valid host on payload returns 200"""

    with client.application.app_context():
        resp = client.delete(
            f"/docker-executor/blacklist",
            data=dumps({
                "host": "example.com:1234"
            })
        )
        expect(resp.status_code).to_equal(200)
