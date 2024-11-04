import os

def get_value(key: str) -> str:
    result = os.getenv(key)
    if result is None:
        raise ValueError(f'Variable {key} is required')
    return result

PROJECT_DOMAIN = get_value("PROJECT_DOMAIN")
PROJECT_NAME = get_value("PROJECT_NAME")
REGISTRY_USERNAME = os.getenv("REGISTRY_USERNAME")
REGISTRY_PASSWORD = os.getenv("REGISTRY_PASSWORD")
REGISTRY_HOSTNAME = os.getenv("REGISTRY_HOSTNAME")
REGISTRY_NAMESPACE = os.getenv("REGISTRY_NAMESPACE")
DOCKER_IMAGE_PREFIX = f'{REGISTRY_HOSTNAME}/{REGISTRY_NAMESPACE}/{PROJECT_NAME}'
DEPLOY_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(DEPLOY_DIR)
ENV_DIR = os.path.join(PROJECT_DIR, 'environment')
COMPOSE_DIR = os.path.join(DEPLOY_DIR, 'compose')

PROD_APP_PATH = f'/app/{PROJECT_NAME}'

PROD_ENV_FILE = f'{ENV_DIR}/env.prod'
BASE_ENV_FILE = f'{ENV_DIR}/env.base'
