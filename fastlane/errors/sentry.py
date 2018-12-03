# import sentry_sdk
from raven import Client

from fastlane.errors import ErrorReporter


class SentryErrorHandler(ErrorReporter):
    def __init__(self, app):
        super(SentryErrorHandler, self).__init__(app)

        self.client = None
        self.send = True

        if app.config["SENTRY_DSN"] == "":
            self.send = False
        else:
            app.logger.info(
                "Sentry configured properly.", sentry_dsn=app.config["SENTRY_DSN"]
            )
            self.client = Client(app.config["SENTRY_DSN"], auto_log_stacks=True)

    def report(self, err, metadata=None):
        if not self.send:
            return

        if metadata is None:
            metadata = {}

        exc_info = (err.__class__, err, err.__traceback__)
        self.client.captureException(exc_info=exc_info, extra=metadata)

        # with sentry_sdk.configure_scope() as scope:
        # scope.level = "error"

        # for key, val in metadata.items():
        # scope.set_extra(key, val)

        # sentry_sdk.capture_exception(err)
