from json import loads

from preggy import expect
from redis.exceptions import ConnectionError

from easyq.models import db


def test_healthcheck1(client):
    """Test healthcheck works if redis is live"""

    rv = client.get('/healthcheck', follow_redirects=True)
    expect(rv.status_code).to_equal(200)

    obj = loads(rv.data)
    expect(obj['redis']).to_be_true()
    expect(obj['mongo']).to_be_true()
    expect(obj['errors']).to_be_empty()


def test_healthcheck2(client):
    """Test healthcheck works if redis is offline"""

    client.application.redis.disconnect()

    rv = client.get('/healthcheck', follow_redirects=True)
    expect(rv.status_code).to_equal(500)

    obj = loads(rv.data)
    expect(obj['redis']).to_be_false()
    expect(obj['mongo']).to_be_true()
    expect(obj['errors']).to_length(1)

    err = obj['errors'][0]
    expect(
        err['message']).to_equal('FakeRedis is emulating a connection error.')
    expect(err['source']).to_equal('redis')


# def test_healthcheck3(client):
# """Test healthcheck works if mongo is offline"""

# with client.application.app_context():
# import ipdb
# ipdb.set_trace()
# x = 1
# # client.application.redis.disconnect()

# rv = client.get('/healthcheck', follow_redirects=True)
# expect(rv.status_code).to_equal(500)

# obj = loads(rv.data)
# expect(obj['redis']).to_be_false()
# expect(obj['mongo']).to_be_true()
# expect(obj['errors']).to_length(1)

# err = obj['errors'][0]
# expect(
# err['message']).to_equal('FakeRedis is emulating a connection error.')
# expect(err['source']).to_equal('redis')
