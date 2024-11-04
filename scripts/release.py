from scripts.utils import request, save_env_option
from scripts.constants import PROJECT_NAME
import os

CURRENT_VERION = int(os.getenv('PROJECT_VERSION', 1))
SENTRY_ORG = os.getenv('SENTRY_ORG', 'grey')
SENTRY_URL = f'https://sentry.io/api/0/organizations/{SENTRY_ORG}/releases/'
SENTRY_RELEASE_TOKEN = os.getenv('SENTRY_RELEASE_TOKEN')
SENTRY_PROJECTS = str(os.getenv('SENTRY_PROJECTS', f'{PROJECT_NAME}-frontend,{PROJECT_NAME}-django'))

def sentry_release(version: str):
    print(f'Sending verion {version} to Sentry')
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


def update_sentry_release():
    next_version = CURRENT_VERION + 1
    print(f'Releasing version {next_version}')
    save_env_option('PROJECT_VERSION', str(next_version))
    save_env_option('NEXT_PUBLIC_VERSION', str(next_version))
    sentry_release(str(next_version))