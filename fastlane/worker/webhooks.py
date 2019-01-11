# 3rd Party
from requests import Request, Session


class WebhooksDispatchError(RuntimeError):
    def __init__(self, status_code, method, url, body, headers, error=None):
        super(WebhooksDispatchError, self).__init__("Webhook dispatch error")
        self.status_code = status_code
        self.method = method
        self.url = url
        self.body = body
        self.headers = headers
        self.error = error

    def __str__(self):
        if self.error is None:
            return (
                f"The {self.method.upper()} request to {self.url} with body"
                f' of "{self.body[:10]}..." failed with status code of {self.status_code}.'
            )

        error = "{}: {}".format(type(self.error).__name__, self.error)

        return (
            f"The {self.method.upper()} request to {self.url} with body "
            f'of "{self.body[:10]}..." failed with exception of {error}.'
        )

    def __repr__(self):
        return str(self)


class Response:
    def __init__(self, status_code, body, headers):
        self.status_code = status_code
        self.body = body
        self.headers = headers


class WebhooksDispatcher:
    def dispatch(self, method, url, body, headers, timeout=1):
        try:
            session = Session()

            req = Request(method, url, data=body, headers=headers)
            prepped = session.prepare_request(req)
            prepped.body = body

            resp = session.send(prepped, timeout=timeout, verify=False)

            if resp.status_code > 399:
                raise WebhooksDispatchError(
                    resp.status_code, method, url, body, headers
                )

            return Response(resp.status_code, resp.text, resp.headers)
        except Exception as err:
            if isinstance(err, WebhooksDispatchError):
                raise err
            raise WebhooksDispatchError(500, method, url, body, headers, error=err)
