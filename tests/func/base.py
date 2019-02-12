import time

import tests.fixtures.func  # NOQA pylint: disable=unused-import


def wait_until(condition, *args, interval=0.1, timeout=1):
    start = time.time()
    while not condition(*args) and time.time() - start < timeout:
        time.sleep(interval)
