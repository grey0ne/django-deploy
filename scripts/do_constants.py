import os
from scripts.constants import PROJECT_NAME

PROJECT_DESCRIPTION = f"{PROJECT_NAME} project"

DO_TOKEN = os.getenv("DO_TOKEN", '')
REGION = os.getenv("DO_REGION", "ams3")

DROPLET_OS_IMAGE = os.getenv("DO_DROPLET_OS_IMAGE", "debian-12-x64")
DROPLET_SIZE = os.getenv("DO_SIZE", "s-1vcpu-1gb")
DROPLET_NAME = f"{PROJECT_NAME}-app"
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