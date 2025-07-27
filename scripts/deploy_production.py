from scripts.shell_commands import (
    INIT_SWARM_SCRIPT, RELOAD_NGINX
)
from scripts.commands import (
    copy_to_remote, get_image_hash, update_swarm,
    collect_static, upload_images, login_registry, build_images
)
from scripts.helpers import run_command, run_remote_commands
from scripts.printing import print_status
from scripts.constants import (
    DEPLOY_DIR, PROD_APP_PATH, PROJECT_DOMAIN, COMPOSE_DIR,
    DOCKER_IMAGE_PREFIX, PROJECT_NAME, BASE_ENV_FILE, PROD_ENV_FILE, COMPOSE_PROFILES, EXTRA_DOMAINS
)
from scripts.release import release_version, update_version
from scripts.docker_compose import render_production_compose_file
from scripts.nginx.configuration import (
    render_app_prod_nginx_conf, render_centrifugo_prod_nginx_conf, render_extra_domain_prod_nginx_conf
)


def app_prod_nginx_conf():
    render_app_prod_nginx_conf(f'{DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}.conf')
    copy_to_remote(f'{DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}.conf', f'/app/balancer/conf/{PROJECT_NAME}.conf')
    run_command(f"rm {DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}.conf")

def centrifugo_prod_nginx_conf():
    render_centrifugo_prod_nginx_conf(f'{DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}_centrifugo.conf')
    copy_to_remote(f'{DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}_centrifugo.conf', f'/app/balancer/conf/{PROJECT_NAME}_centrifugo.conf')
    run_command(f"rm {DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}_centrifugo.conf")

def extra_domain_prod_nginx_conf(domain: str):
    render_extra_domain_prod_nginx_conf(f'{DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}_{domain}.conf', domain)
    copy_to_remote(f'{DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}_{domain}.conf', f'/app/balancer/conf/{PROJECT_NAME}_{domain}.conf')
    run_command(f"rm {DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}_{domain}.conf")


def update_prod_nginx():
    print_status(f"Copying nginx config to {PROJECT_DOMAIN}")
    app_prod_nginx_conf()
    if "centrifugo" in COMPOSE_PROFILES:
        centrifugo_prod_nginx_conf()
    for domain in EXTRA_DOMAINS:
        extra_domain_prod_nginx_conf(domain)

    print_status("Reloading nginx")
    run_remote_commands([RELOAD_NGINX, ])


def deploy_production():
    new_version = update_version()

    build_images()
    login_registry()
    upload_images()

    # Release version after build to avoid debug releases
    release_version(new_version)
    collect_static()

    django_image = get_image_hash(f'{DOCKER_IMAGE_PREFIX}-django')
    nextjs_image = get_image_hash(f'{DOCKER_IMAGE_PREFIX}-nextjs')
    render_production_compose_file(django_image, nextjs_image)
    print_status(f"Deploying to {PROJECT_DOMAIN}")
    run_remote_commands([f"mkdir -p {PROD_APP_PATH}", f"mkdir -p {PROD_APP_PATH}/backend_data"])
    print_status(f"Copying compose files to {PROJECT_DOMAIN}")

    copy_to_remote(f'{COMPOSE_DIR}/prod.yml', f'{PROD_APP_PATH}/prod.yml')
    run_command(f"rm {COMPOSE_DIR}/prod.yml")

    copy_to_remote(f"{DEPLOY_DIR}/prod-scripts/certbot_renew.sh", "/etc/cron.daily")

    print_status(f"Copying env files to {PROJECT_DOMAIN}")
    copy_to_remote(BASE_ENV_FILE, f"{PROD_APP_PATH}/env.base")
    copy_to_remote(PROD_ENV_FILE, f"{PROD_APP_PATH}/env")
    run_remote_commands([INIT_SWARM_SCRIPT])
    print_status("Update django image for migrations")
    run_remote_commands([f"docker pull {DOCKER_IMAGE_PREFIX}-django"])
    print_status("Perform migrations")
    run_remote_commands([f"docker run --rm -i --env-file={PROD_APP_PATH}/env.base --env-file={PROD_APP_PATH}/env {DOCKER_IMAGE_PREFIX}-django python manage.py migrate"])
    update_swarm(f'{PROD_APP_PATH}/prod.yml', PROJECT_NAME)

    update_prod_nginx()