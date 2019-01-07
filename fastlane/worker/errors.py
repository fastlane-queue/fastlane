class HostUnavailableError(RuntimeError):
    def __init__(self, host, port, error):
        self.host = host
        self.port = port
        self.error = error
        self.message = f"Connection to host {self.host}:{self.port} failed with error: {self.error}"
