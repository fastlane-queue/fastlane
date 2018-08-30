class ExecutionResult:
    class Status:
        created = 'created'
        running = 'running'
        failed = 'failed'
        done = 'done'

    def __init__(self, status):
        self.status = status
        self.exit_code = None
        self.started_at = None
        self.finished_at = None

        self.log = ''
        self.error = ''

    def set_log(self, log):
        self.log = log
