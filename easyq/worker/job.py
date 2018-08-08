from flask import current_app


def run_job(container, command):
    print(current_app.name)
    print(f'Container: {container} Command: {command}')
