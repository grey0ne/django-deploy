from scripts.http_request import request
from scripts.helpers import print_status, save_env_option
from scripts.constants import PROJECT_NAME, ENV_DIR
import os

CURRENT_VERION = int(os.getenv('PROJECT_VERSION', 1))
SENTRY_ORG = os.getenv('SENTRY_ORG', 'grey')
SENTRY_URL = f'https://sentry.io/api/0/organizations/{SENTRY_ORG}/releases/'
SENTRY_RELEASE_TOKEN = os.getenv('SENTRY_RELEASE_TOKEN')
SENTRY_PROJECTS = str(os.getenv('SENTRY_PROJECTS', f'{PROJECT_NAME}-frontend,{PROJECT_NAME}-django'))
VERSION_FILE = os.path.join(ENV_DIR, 'version')

def sentry_release(version: str):
    print_status(f'Sending verion {version} to Sentry. Projects {SENTRY_PROJECTS.replace(",", ", ")}')
    if not SENTRY_RELEASE_TOKEN:
        raise ValueError('SENTRY_RELEASE_TOKEN is not set')
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
    save_env_option('PROJECT_VERSION', str(version))
    save_env_option('NEXT_PUBLIC_VERSION', str(version))

def update_sentry_release():
    current_version = read_version()
    next_version = increment_version(current_version)
    save_version(next_version)
    print_status(f'Releasing version {next_version} of {PROJECT_NAME}')
    sentry_release(next_version)