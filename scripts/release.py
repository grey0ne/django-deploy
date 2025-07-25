from scripts.http_request import request
from scripts.helpers import save_env_option, run_command
from scripts.printing import print_status, print_warning
from scripts.constants import (
    PROJECT_NAME, SENTRY_PROJECTS, SENTRY_RELEASE_TOKEN, SENTRY_URL, VERSION_FILE
)

def sentry_release(version: str):
    if not SENTRY_RELEASE_TOKEN:
        print_warning('SENTRY_RELEASE_TOKEN is not set. Skipping Sentry release.')
        return
    print_status(f'Sending verion {version} to Sentry. Projects {SENTRY_PROJECTS.replace(",", ", ")}')
    headers = {
        'Authorization': f'Bearer {SENTRY_RELEASE_TOKEN}',
    }
    request(
        url=SENTRY_URL,
        headers=headers,
        data={
            'version': version,
            'projects': SENTRY_PROJECTS.split(',')
        },
        method='POST',
    )

def increment_version(version: str) -> str:
    last_digit = int(version.split('.')[-1])
    return '.'.join(version.split('.')[:-1] + [str(last_digit + 1)])

def read_version():
    with open(VERSION_FILE, 'r') as f:
        return f.read()

def save_version(version: str):
    with open(VERSION_FILE, 'w') as f:
        f.write(version)
    save_env_option('PROJECT_VERSION', str(version), create=True)
    save_env_option('NEXT_PUBLIC_VERSION', str(version), create=True)

def commit_version(version: str):
    run_command(f'git commit environment/version -m "Version {version}"')

def update_version():
    current_version = read_version()
    next_version = increment_version(current_version)
    save_version(next_version)
    print_status(f'Version of {PROJECT_NAME} updated to {next_version}')
    return next_version

def release_version(version: str):
    commit_version(version)
    print_status(f'Releasing version {version} of {PROJECT_NAME}')
    sentry_release(version)