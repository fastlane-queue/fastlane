# Standard Library
from json import loads

# 3rd Party
from preggy import expect


def test_status(client):
    """Test the status response"""

    resp = client.get("/status/")
    expect(resp.status_code).to_equal(200)

    data = loads(resp.data)
    expect(data["containers"]['running']).to_length(0)
