class ErrorReporter:
    def __init__(self, app):
        self.app = app

    def report(self, err, metadata=None):
        raise NotImplementedError()
