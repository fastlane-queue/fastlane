from preggy import expect
from redis.exceptions import ConnectionError


def test_healthcheck1(client):
    """Test healthcheck works if redis is live"""

    rv = client.get('/healthcheck/')
    expect(rv.data).to_equal('WORKING')


def test_healthcheck2(client):
    """Test healthcheck works if redis is offline"""

    client.application.redis.disconnect()

    with expect.error_to_happen(
            ConnectionError,
            message="FakeRedis is emulating a connection error."):
        client.get('/healthcheck/')
