import subprocess
from subprocess import PIPE
from scripts.constants import (
    PROJECT_DOMAIN, COMPOSE_DIR, DEPLOY_DIR, PROD_ENV_FILE,
    BASE_ENV_FILE, PROJECT_NAME, DOCKER_IMAGE_PREFIX, PROJECT_DIR
)
from scripts.commands import RELOAD_NGINX, LOGIN_REGISTRY_SCRIPT
import fileinput


def save_env_option(option_name: str, value: str, env_file: str = PROD_ENV_FILE):
    option_found = False
    with fileinput.input(files=(env_file, ), encoding="utf-8", inplace=True) as f:
        for line in f:
            if f'{option_name}=' in line:
                result = f'{option_name}={value}\n'
                option_found=True
            else:
                result = line
            print(result, end='')
        if not option_found:
            raise Exception('Option not found')


def run_command(command: str):
    subprocess.run(command, shell=True, check=True)

def run_remote_commands(commands: list[str]):
    ssh_command = ['ssh', f'root@{PROJECT_DOMAIN}', "bash -s"]
    command = "\n".join(commands)
    p = subprocess.run(ssh_command, stdout=PIPE, input=command, encoding='ascii')
    if p.stdout:
        print(p.stdout)

def copy_to_remote(source: str, destination: str):
    run_command(f'scp {source} root@{PROJECT_DOMAIN}:{destination}')

def get_image_hash(image_name: str) -> str:
    command = ["docker", "inspect", "--format={{index .RepoDigests 0}}", image_name]
    p = subprocess.run(command, stdout=PIPE, encoding='ascii')
    if p.stdout:
        return p.stdout.strip()
    return ""

def print_status(msg: str):
    print(f"\033[0;32m{msg}\033[0m")

def reload_nginx():
    print_status("Reloading nginx")
    run_remote_commands([RELOAD_NGINX, ])

def update_swarm(compose_file: str, stack_name: str):
    print_status(f"Updating {stack_name} swarm")
    STACK_COMMAND = f"docker stack config -c {compose_file} | docker stack deploy --with-registry-auth --detach=false -c - {stack_name}"
    print_status(STACK_COMMAND)
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


def envsubst(from_file: str, to_file: str, variables: list[str] = []):
    if variables:
        variables_str = f"'{",".join([f'${var}' for var in variables])}'"
    else:
        variables_str = ""
    run_command(f'envsubst {variables_str} < {from_file} > {to_file}')
