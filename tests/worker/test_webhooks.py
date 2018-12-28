# 3rd Party
import requests_mock
from preggy import expect

# Fastlane
import fastlane.worker.webhooks as webhooks


@requests_mock.Mocker(kw="rm")
def test_webhooks(**kwargs):
    """Test webhooks returns a response"""
    rm = kwargs["rm"]
    url = "http://some.test.url"
    text = "whatever"
    status_code = 201
    headers = {"qwe": "rty"}
    rm.get(url, text=text, status_code=status_code, headers=headers)

    h = webhooks.WebhooksDispatcher()
    r = h.dispatch("get", url, text, {})

    expect(r.status_code).to_equal(status_code)
    expect(r.body).to_equal(text)
    expect(r.headers).to_be_like(headers)
