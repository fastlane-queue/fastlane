import time
import difflib
from json import loads

# 3rd Party
import pytest
import requests
from pymongo import MongoClient
from preggy import assertion
from colorama import Fore, Style


@pytest.fixture(autouse=True)
def cleanup():
    mongo_client = MongoClient("localhost", 27355)
    database = mongo_client.fastlane_test
    database.Task.drop()
    database.Job.drop()

    yield


class RequestClient:
    def __init__(self):
        self._client = requests.Session()

    def get(self, url, headers=None, absolute=False):
        abs_url = url

        if not absolute:
            abs_url = f"http://localhost:10000/{url.lstrip('/')}"
        response = self._client.get(abs_url, headers=headers)

        return response.status_code, response.text, response.headers

    def post(self, url, data, headers=None, absolute=False):
        abs_url = url

        if not absolute:
            abs_url = f"http://localhost:10000/{url.lstrip('/')}"
        response = self._client.post(abs_url, json=data, headers=headers)

        return response.status_code, response.text, response.headers


@pytest.fixture()
def client():
    yield RequestClient()


def __show_diff(expected, actual):
    seqm = difflib.SequenceMatcher(None, expected, actual)
    output = [Style.RESET_ALL]
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append(seqm.a[a0:a1])
        elif opcode == 'insert':
            output.append(Fore.GREEN + seqm.b[b0:b1] + Style.RESET_ALL)
        elif opcode == 'delete':
            output.append(Fore.RED + seqm.a[a0:a1] + Style.RESET_ALL)
        elif opcode == 'replace':
            output.append(Fore.RED + seqm.a[a0:a1] + Fore.GREEN +
                          seqm.b[b0:b1] + Style.RESET_ALL)
        else:
            raise RuntimeError("unexpected opcode")
    return ''.join(output)


def __validate(topic, execution, **arguments):
    errors = []
    for key, value in arguments.items():
        val = execution[key]
        if isinstance(val, (bytes, str)):
            val = val.strip()
        if val != value:
            if isinstance(val, (bytes, str)):
                diff = __show_diff(value, val)
                errors.append(
                    f'{key} field:\n\tExpected: {value}{Style.RESET_ALL}\n\tActual:   {val}\n\tDiff:     {diff}\n'
                    '\t(diff: red=text to remove, green=text to add)')
            else:
                errors.append(
                    f'{key} field:\n\tExpected: {value}{Style.RESET_ALL}\n\tActual:   {val}'
                )

    if errors:
        error_msg = '\n'.join(errors)
        raise AssertionError(
            f'Execution did not match expectations!\n{Style.RESET_ALL}'
            f'URL: {topic}\n\n{error_msg}')


@assertion
def to_have_finished_with(topic, cli, timeout=20, **kw):
    start = time.time()

    last_obj = None
    while time.time() - start < timeout:
        status_code, body, _ = cli.get(topic, absolute=True)

        if status_code != 200:
            raise AssertionError(
                f"{topic} could not be found (status: {status_code}).")

        last_obj = loads(body)

        try:
            if __validate(topic, last_obj['execution'], **kw):
                return
        except AssertionError:
            pass

        time.sleep(0.5)

    __validate(topic, last_obj['execution'], **kw)


@assertion
def to_have_execution(topic, cli, execution, timeout=20):
    start = time.time()

    last_obj = None
    while time.time() - start < timeout:
        status_code, body, _ = cli.get(topic, absolute=True)

        if status_code != 200:
            raise AssertionError(
                f"{topic} could not be found (status: {status_code}).")

        last_obj = loads(body)
        if last_obj['job']['executions']:
            ex = last_obj['job']['executions'][0]
            execution['url'] = ex['url']
            execution['executionId'] = ex['executionId']
            return

        time.sleep(0.5)

    raise AssertionError(f'Execution for job {topic} has not started.')
