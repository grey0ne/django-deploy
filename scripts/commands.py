from scripts.constants import (
    REGISTRY_PASSWORD, REGISTRY_HOSTNAME, REGISTRY_USERNAME,
    DOCKER_IMAGE_PREFIX, PROD_APP_PATH, PROJECT_NAME,
    PROJECT_DIR, PROJECT_DOMAIN, PROD_ENV_FILE, BASE_ENV_FILE
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

LOGIN_REGISTRY = f"""
{PRINT_COMMAND}
print_status "Login to registry"
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
print_status "Update image for migrations"
docker pull {DOCKER_IMAGE_PREFIX}-django
print_status "Perform migrations"
docker run --rm -i --env-file={PROD_APP_PATH}/env.base --env-file={PROD_APP_PATH}/env {DOCKER_IMAGE_PREFIX}-django python manage.py migrate
"""

INIT_SWARM_SCRIPT = f"""
{PRINT_COMMAND}
{GET_ADDR}
{LOGIN_REGISTRY}
{JOIN_SWARM}
"""

COLLECT_STATIC_SCRIPT = PRINT_COMMAND + f"""
print_status "Collecting static files for django"
docker run --rm -i --env-file={BASE_ENV_FILE} --env-file={PROD_ENV_FILE} -e BUILD_STATIC=true -v ./backend:/app/src {PROJECT_NAME}-django python manage.py collectstatic --noinput
"""

CHECK_BUILD_STATUS = """
    BUILD_RESULT_STATUS=$?
    if [ ${BUILD_RESULT_STATUS} -ne 0 ]; then
        print_error "$1 Build failed!"
        exit "${BUILD_RESULT_STATUS}"
    fi
"""
BUILD_IMAGE_COMMAND = PRINT_COMMAND + """
function build_image () {
""" + f"""
    set -e
    print_status "Building $1"
    docker build --secret id=sentry_auth,env=SENTRY_AUTH_TOKEN  -t {DOCKER_IMAGE_PREFIX}-$1 -f $2 $3  --platform linux/amd64
    {CHECK_BUILD_STATUS}
""" + """
}
"""


BUILD_IMAGES_SCRIPT = f"""
{PRINT_COMMAND}
{BUILD_IMAGE_COMMAND}

print_status "Building images"
export DOCKER_CLI_HINTS="false"
build_image "django" "{PROJECT_DIR}/backend/Dockerfile.prod" "backend"
cd {PROJECT_DIR}/spa
npm run build
cd {PROJECT_DIR}
build_image "nextjs" "{PROJECT_DIR}/spa/Dockerfile.prod" "spa"

{LOGIN_REGISTRY}
print_status "Pushing images to registry"
docker push {DOCKER_IMAGE_PREFIX}-django
docker push {DOCKER_IMAGE_PREFIX}-nextjs
""" 


RELOAD_NGINX = f"""
NGINX_CONTAINER=$(docker ps -q -f name=nginx)
docker exec $NGINX_CONTAINER nginx -s reload
"""

SETUP_CERTBOT = f"""
CERTS_VOLUME=/app/certbot/certificates
CHALLENGE_VOLUME=/app/certbot/challenge
docker run --rm --name temp_certbot -v $CERTS_VOLUME:/etc/letsencrypt -v $CHALLENGE_VOLUME:/tmp/letsencrypt certbot/certbot:v1.14.0 certonly --non-interactive --webroot --agree-tos --keep-until-expiring --text --email sergey.lihobabin@gmail.com -d {PROJECT_DOMAIN} -w /tmp/letsencrypt
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