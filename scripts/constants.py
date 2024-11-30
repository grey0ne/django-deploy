import os

def get_config_value(key: str, default: str | None = None) -> str:
    result = os.getenv(key)
    if result is None:
        if default is not None:
            return default
        raise ValueError(f'Variable {key} is required')
    return result

PROJECT_DOMAIN = get_config_value("PROJECT_DOMAIN")
PROJECT_NAME = get_config_value("PROJECT_NAME")
REGISTRY_USERNAME = os.getenv("REGISTRY_USERNAME")
REGISTRY_PASSWORD = os.getenv("REGISTRY_PASSWORD")
REGISTRY_HOSTNAME = os.getenv("REGISTRY_HOSTNAME")
REGISTRY_NAMESPACE = os.getenv("REGISTRY_NAMESPACE")
DOCKER_IMAGE_PREFIX = f'{REGISTRY_HOSTNAME}/{REGISTRY_NAMESPACE}/{PROJECT_NAME}'
DEPLOY_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = os.path.dirname(DEPLOY_DIR)
ENV_DIR = os.path.join(PROJECT_DIR, 'environment')
COMPOSE_DIR = os.path.join(DEPLOY_DIR, 'compose')
VERSION_FILE = os.path.join(ENV_DIR, 'version')

PROD_APP_PATH = f'/app/{PROJECT_NAME}'

PROD_ENV_FILE = f'{ENV_DIR}/env.prod'
BASE_ENV_FILE = f'{ENV_DIR}/env.base'

# Constants for DigitalOcean
PROJECT_DESCRIPTION = f"{PROJECT_NAME} project"

DO_TOKEN = os.getenv("DO_TOKEN", '')
DO_REGION = os.getenv("DO_REGION", "ams3")

DROPLET_OS_IMAGE = os.getenv("DO_DROPLET_OS_IMAGE", "debian-12-x64")
DROPLET_SIZE = os.getenv("DO_SIZE", "s-1vcpu-1gb")
DROPLET_NAME = get_config_value("DO_DROPLET_NAME", default=f"{PROJECT_NAME}-app")
DROPLET_TAGS = ["auto-created"]
SSH_FINGERPRINT = os.getenv("DO_KEY_FINGERPRINT")
PG_NODES_NUM = 1
PG_VERSION = "16"
PG_SIZE = "db-s-1vcpu-1gb"
PG_STORAGE_SIZE = 15000 # 15GB
PG_CLUSTER_NAME = os.getenv("DATABASE_CLUSTER", "communal-db")
PG_DB_NAME = os.getenv("DATABASE_NAME", PROJECT_NAME)
PG_USERNAME = os.getenv("DATABASE_USER", '')
STATUS_CHECK_INTERVAL = 1 # in seconds

DO_API_DOMAIN = "https://api.digitalocean.com"
DROPLETS_URL = f"{DO_API_DOMAIN}/v2/droplets"

DO_HEADERS = {
    "Authorization": f"Bearer {DO_TOKEN}",
    "Content-Type": "application/json"
}

# Constants for Sentry
SENTRY_ORG = os.getenv('SENTRY_ORG', 'grey')
SENTRY_URL = f'https://sentry.io/api/0/organizations/{SENTRY_ORG}/releases/'
SENTRY_RELEASE_TOKEN = os.getenv('SENTRY_RELEASE_TOKEN')
SENTRY_PROJECTS = str(os.getenv('SENTRY_PROJECTS', f'{PROJECT_NAME}-frontend,{PROJECT_NAME}-django'))

S3_ENDPOINT_URL = os.getenv('S3_ENDPOINT_URL')
S3_ACCESS_KEY_ID = os.getenv('S3_ACCESS_KEY_ID')
S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')
S3_MEDIA_BUCKET = os.getenv('S3_MEDIA_BUCKET')
S3_ACL = os.getenv('S3_ACL', 'private')
