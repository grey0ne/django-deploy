from scripts.constants import (
    PROJECT_DOMAIN, COMPOSE_DIR, DEPLOY_DIR, DOCKER_IMAGE_PREFIX,
    BASE_ENV_FILE, PROD_ENV_FILE, PROJECT_NAME, PROJECT_DIR
)
from scripts.helpers import run_command, print_status, run_remote_commands
from scripts.shell_commands import RELOAD_NGINX, LOGIN_REGISTRY_SCRIPT
import subprocess
from subprocess import PIPE


def copy_to_remote(source: str, destination: str):
    run_command(f'scp {source} root@{PROJECT_DOMAIN}:{destination}')

def get_image_hash(image_name: str) -> str:
    command = ["docker", "inspect", "--format={{index .RepoDigests 0}}", image_name]
    p = subprocess.run(command, stdout=PIPE, encoding='ascii')
    if p.stdout:
        return p.stdout.strip()
    return ""


def reload_nginx():
    print_status("Reloading nginx")
    run_remote_commands([RELOAD_NGINX, ])

def update_swarm(compose_file: str, stack_name: str):
    print_status(f"Updating {stack_name} swarm")
    STACK_COMMAND = f"docker stack config -c {compose_file} | docker stack deploy --with-registry-auth --detach=false -c - {stack_name}"
    run_remote_commands([STACK_COMMAND, ])
    print_status("Prune images")
    run_remote_commands(['docker image prune -f',])

def setup_balancer():
    print_status("Copying balancer files")
    run_remote_commands([
        f"mkdir -p /app/balancer",
        f"mkdir -p /app/balancer/conf",
    ])
    copy_to_remote(f'{COMPOSE_DIR}/prod_balancer.yml', '/app/balancer/compose.yml')
    copy_to_remote(f'{DEPLOY_DIR}/nginx/conf/balancer.conf', '/app/balancer/conf/default.conf')
    update_swarm('/app/balancer/compose.yml', 'balancer')
    reload_nginx()


def collect_static():
    print_status("Collecting static files for django. Uploading static to S3")
    run_command(
        f"docker run --rm -i --env-file={BASE_ENV_FILE} --env-file={PROD_ENV_FILE} -e BUILD_STATIC=true -v ./backend:/app/src {PROJECT_NAME}-django python manage.py collectstatic --noinput"
    )

def upload_images():
    print_status("Uploading images to registry")
    run_command(f"docker push {DOCKER_IMAGE_PREFIX}-django")
    run_command(f"docker push {DOCKER_IMAGE_PREFIX}-nextjs")

def login_registry():
    run_command(LOGIN_REGISTRY_SCRIPT)

def build_image(service: str, dockerfile: str, context: str):
    print_status(f"Building image for {service}")
    command = f"""
        export DOCKER_CLI_HINTS="false"
        docker build -t {DOCKER_IMAGE_PREFIX}-{service} -f {dockerfile} {context}  --platform linux/amd64
    """
    run_command(command)

def build_images():
    build_image("django", f"{PROJECT_DIR}/backend/Dockerfile.prod", f"{PROJECT_DIR}/backend")
    #print_status("Building nextjs app")
    #run_command(f"""
        #cd {PROJECT_DIR}/spa
        #npm run build
        #cd {PROJECT_DIR}
    #""")
    build_image("nextjs", f"{PROJECT_DIR}/spa/Dockerfile.prod", f"{PROJECT_DIR}/spa")

