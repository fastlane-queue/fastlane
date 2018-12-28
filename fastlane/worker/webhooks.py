# 3rd Party
from requests import Request, Session


class Response:
    def __init__(self, status_code, body, headers=None):
        self.status_code = status_code
        self.body = body
        self.headers = headers

        if self.headers is None:
            self.headers = {}


class WebhooksDispatcher:
    def dispatch(self, method, url, body, headers, timeout=1):
        s = Session()

        req = Request(method, url, data=body, headers=headers)
        prepped = s.prepare_request(req)
        prepped.body = body

        resp = s.send(prepped, timeout=timeout, verify=False)

        return Response(resp.status_code, resp.text, resp.headers)
