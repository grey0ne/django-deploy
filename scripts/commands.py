from scripts.constants import (
    PROJECT_DOMAIN, COMPOSE_DIR, DEPLOY_DIR, DOCKER_IMAGE_PREFIX,
    BASE_ENV_FILE, PROD_ENV_FILE, PROJECT_NAME, PROJECT_DIR, NGINX_CONFIG_DIR,
    COMPOSE_PROFILES, SSL_CERTS_DIR
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


def reload_prod_nginx():
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
    reload_prod_nginx()

def copy_nginx_config(from_path: str, to_path: str):
    print_status(f"Copying {from_path} to {to_path}")
    run_command(
        f"envsubst '$PROJECT_NAME,$PROJECT_DOMAIN' < {from_path} > {to_path}"
    )

def update_dev_nginx():
    run_command(
        f"mkdir -p {NGINX_CONFIG_DIR}"
    )
    copy_nginx_config(f"{DEPLOY_DIR}/nginx/conf/nginx_dev.template", f"{NGINX_CONFIG_DIR}/{PROJECT_NAME}.conf")
    if "centrifugo" in COMPOSE_PROFILES:
        copy_nginx_config(f"{DEPLOY_DIR}/nginx/conf/centrifugo_dev.template", f"{NGINX_CONFIG_DIR}/{PROJECT_NAME}_centrifugo.conf")

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
    build_image("nextjs", f"{PROJECT_DIR}/spa/Dockerfile.prod", f"{PROJECT_DIR}/spa")


def gen_cert(name:str, domain:str):
    print_status(f"Generating cert {name} for {domain}")
    run_command(
        f"{DEPLOY_DIR}/generate_certs.sh {name} {domain}"
    )

def add_cert_to_trusted(cert_path: str):
    print_status(f"Adding cert to trusted {cert_path}")
    run_command(
        f"sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain {cert_path}"
    )

def update_hosts(domain: str):
    print_status(f"Updating hosts file with {domain}")
    run_command(
        f"{DEPLOY_DIR}/update_hosts.sh addhost {domain}"
    )

def generate_dev_certs():
    gen_cert(PROJECT_NAME, PROJECT_DOMAIN)
    gen_cert(f"media_{PROJECT_NAME}", f"media.{PROJECT_DOMAIN}")
    add_cert_to_trusted(f"{SSL_CERTS_DIR}/{PROJECT_NAME}.crt")
    add_cert_to_trusted(f"{SSL_CERTS_DIR}/media_{PROJECT_NAME}.crt")
    update_hosts(PROJECT_DOMAIN)
    update_hosts(f"media.{PROJECT_DOMAIN}")
    if "centrifugo" in COMPOSE_PROFILES:
        gen_cert(f"centrifugo_{PROJECT_NAME}", f"centrifugo.{PROJECT_DOMAIN}")
        add_cert_to_trusted(f"{SSL_CERTS_DIR}/centrifugo_{PROJECT_NAME}.crt")
        update_hosts(f"centrifugo.{PROJECT_DOMAIN}")


def setup_prod_domain_cert(domain: str):
    SETUP_CERTBOT_COMMAND = f"""
    CERTS_VOLUME=/app/certbot/certificates
    CHALLENGE_VOLUME=/app/certbot/challenge
    docker run --rm --name temp_certbot -v $CERTS_VOLUME:/etc/letsencrypt -v $CHALLENGE_VOLUME:/tmp/letsencrypt certbot/certbot:v1.14.0 certonly --non-interactive --webroot --agree-tos --keep-until-expiring --text --email sergey.lihobabin@gmail.com -d {domain} -w /tmp/letsencrypt
    """
    run_remote_commands([ SETUP_CERTBOT_COMMAND, ])