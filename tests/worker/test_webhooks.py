# 3rd Party
import requests
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


@requests_mock.Mocker(kw="rm")
def test_webhooks_2(**kwargs):
    """Test webhooks fail on 500"""
    rm = kwargs["rm"]
    url = "http://some.test.url"
    text = "whatever"
    headers = {"qwe": "rty"}
    rm.get(url, text=text, status_code=500, headers=headers)

    h = webhooks.WebhooksDispatcher()
    msg = 'The GET request to http://some.test.url with body of "whatever..." failed with status code of %d.'
    with expect.error_to_happen(webhooks.WebhooksDispatchError, message=msg % 500):
        h.dispatch("get", url, text, {})

    rm.get(url, text=text, status_code=400, headers=headers)
    with expect.error_to_happen(webhooks.WebhooksDispatchError, message=msg % 400):
        h.dispatch("get", url, text, {})


@requests_mock.Mocker(kw="rm")
def test_webhooks_3(**kwargs):
    """Test webhooks fail on error"""
    rm = kwargs["rm"]
    url = "http://some.test.url"
    text = "whatever"
    rm.get(url, exc=requests.exceptions.ConnectTimeout("something"))

    h = webhooks.WebhooksDispatcher()
    msg = (
        'The GET request to http://some.test.url with body of "whatever..." '
        "failed with exception of ConnectTimeout: something."
    )
    with expect.error_to_happen(webhooks.WebhooksDispatchError, message=msg):
        h.dispatch("get", url, text, {})
