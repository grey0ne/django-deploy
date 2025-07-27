from scripts.constants import (
    PROJECT_DOMAIN, COMPOSE_DIR, DEPLOY_DIR, DOCKER_IMAGE_PREFIX,
    BASE_ENV_FILE, PROD_ENV_FILE, PROJECT_NAME, PROJECT_DIR, NGINX_CONFIG_DIR,
    COMPOSE_PROFILES, SSL_CERTS_DIR, ENV_DIR, EXTRA_DOMAINS
)
from scripts.helpers import run_command, run_remote_commands
from scripts.printing import print_status
from scripts.shell_commands import RELOAD_NGINX, LOGIN_REGISTRY_SCRIPT, GEN_FAKE_CERTS, SETUP_DOCKER
from scripts.nginx.configuration import (
    render_dev_nginx_conf, render_centrifugo_dev_nginx_conf, render_extra_domain_nginx_conf
)
import subprocess
from subprocess import PIPE

S3_BACKUP_COMMAND=f"docker run -it --rm -v {PROJECT_DIR}/backend:/app/src -v {PROJECT_DIR}/deploy:/app/deploy -v {PROJECT_DIR}/backup/s3_backup:/tmp/s3_backup --network {PROJECT_NAME} --env-file {ENV_DIR}/env.base"

def restore_s3_backup(env_file: str):
    command = f"{S3_BACKUP_COMMAND} --env-file {env_file} {PROJECT_NAME}-django python /app/deploy/scripts/s3_upload.py"
    run_command(command)

def create_s3_backup(env_file: str):
    command = f"{S3_BACKUP_COMMAND} --env-file {env_file} {PROJECT_NAME}-django python /app/deploy/scripts/s3_backup.py"
    run_command(command)

def create_s3_dev_bucket():
    command = f"{S3_BACKUP_COMMAND} --env-file {ENV_DIR}/env.dev {PROJECT_NAME}-django python /app/deploy/scripts/s3_create_bucket.py"
    run_command(command)

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


def update_dev_nginx():
    run_command(
        f"mkdir -p {NGINX_CONFIG_DIR}"
    )
    render_dev_nginx_conf(f"{NGINX_CONFIG_DIR}/{PROJECT_NAME}.conf.template")
    if "centrifugo" in COMPOSE_PROFILES:
        render_centrifugo_dev_nginx_conf(f"{NGINX_CONFIG_DIR}/{PROJECT_NAME}_centrifugo.conf.template")
    for domain in EXTRA_DOMAINS:
        render_extra_domain_nginx_conf(f"{NGINX_CONFIG_DIR}/{PROJECT_NAME}_{domain}.conf.template", domain)

def collect_static():
    print_status("Collecting static files for django")
    run_command(
        f"docker run --rm -i --env-file={BASE_ENV_FILE} --env-file={PROD_ENV_FILE} -e BUILD_STATIC=true -v ./backend:/app/src {PROJECT_NAME}-django python manage.py collectstatic --noinput"
    )
    print_status("Uploading static files to S3")
    run_command(
        f"docker run --rm -i --env-file={BASE_ENV_FILE} --env-file={PROD_ENV_FILE} -v ./backend:/app/src -v {PROJECT_DIR}/deploy:/app/deploy {PROJECT_NAME}-django python /app/deploy/scripts/collect_static.py"
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
    build_image("nextjs", f"{PROJECT_DIR}/deploy/docker/Dockerfile.nextjsprod", f"{PROJECT_DIR}/spa")


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
    for domain in EXTRA_DOMAINS:
        cert_name = f"{PROJECT_NAME}_{domain}"
        gen_cert(cert_name, domain)
        add_cert_to_trusted(f"{SSL_CERTS_DIR}/{cert_name}.crt")
        update_hosts(domain)
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


def production_setup():
    print_status("Setting up docker")
    run_remote_commands([ SETUP_DOCKER, ])
    setup_balancer()
    print_status(f"Setting up certbot for domain {PROJECT_DOMAIN}")
    run_remote_commands([
        f"mkdir -p /app/certbot/certificates",
        f"mkdir -p /app/certbot/challenge",
    ])
    setup_prod_domain_cert(PROJECT_DOMAIN)
    if "centrifugo" in COMPOSE_PROFILES:
        setup_prod_domain_cert(f"centrifugo.{PROJECT_DOMAIN}")
    print_status(f"Copying fake certs to dummy folder")
    run_remote_commands([ GEN_FAKE_CERTS, ])
    reload_prod_nginx()