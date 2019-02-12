class HostUnavailableError(RuntimeError):
    def __init__(self, host, port, error):
        msg = f"Connection to host {host}:{port} failed with error: {error}"
        super(HostUnavailableError, self).__init__(msg)
        self.host = host
        self.port = port
        self.error = error
        self.message = f"Connection to host {self.host}:{self.port} failed with error: {self.error}"


class NoAvailableHostsError(RuntimeError):
    pass


class ContainerUnavailableError(RuntimeError):
    pass
