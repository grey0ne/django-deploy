from scripts.constants import (
    REGISTRY_PASSWORD, REGISTRY_HOSTNAME, REGISTRY_USERNAME,
    DOCKER_IMAGE_PREFIX, PROD_APP_PATH, PROJECT_DOMAIN
)

PRINT_COMMAND = """
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    NC='\033[0m'

    function print_status () {
        echo "${GREEN}$1${NC}"
    }

    function print_error () {
        echo "${RED}$1${NC}" >&2
    }
"""

GET_ADDR = """
for ADDR in $(ip addr show "eth0" | awk '/inet / {print $2}')
do
    if [[ $ADDR == *16 ]]
    then
        RESULT_ADDR=${ADDR::-3}
    fi
done
"""

LOGIN_REGISTRY_SCRIPT = f"""
{PRINT_COMMAND}
print_status "Login to registry {REGISTRY_HOSTNAME}"
echo {REGISTRY_PASSWORD} | docker login {REGISTRY_HOSTNAME} --username {REGISTRY_USERNAME} --password-stdin
"""

JOIN_SWARM = """
if [ "$(docker info --format '{{.Swarm.LocalNodeState}}')" = "active" ]; then
    print_status "Swarm already initialized"
else
    print_status "Initializing swarm"
    docker swarm init --advertise-addr $RESULT_ADDR
fi
"""

PERFORM_MIGRATIONS = f"""
{PRINT_COMMAND}
print_status "Update django image for migrations"
docker pull {DOCKER_IMAGE_PREFIX}-django
print_status "Perform migrations"
docker run --rm -i --env-file={PROD_APP_PATH}/env.base --env-file={PROD_APP_PATH}/env {DOCKER_IMAGE_PREFIX}-django python manage.py migrate
"""

INIT_SWARM_SCRIPT = f"""
{PRINT_COMMAND}
{GET_ADDR}
{LOGIN_REGISTRY_SCRIPT}
{JOIN_SWARM}
"""

RELOAD_NGINX = f"""
NGINX_CONTAINER=$(docker ps -q -f name=nginx)
docker exec $NGINX_CONTAINER nginx -s reload
"""

GEN_FAKE_CERTS = f"""
cp -r /app/certbot/certificates/live/{PROJECT_DOMAIN} /app/certbot/certificates/live/dummy
"""

SETUP_DOCKER = """
if [ -x "$(command -v docker)" ]; then
   echo "Docker already installed"
else
    # Add Docker's official GPG key:
    apt update
    apt upgrade -y
    apt install ca-certificates curl -y
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    # Add the repository to Apt sources:
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
fi
"""