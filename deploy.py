from scripts.shell_commands import (
    INIT_SWARM_SCRIPT, PERFORM_MIGRATIONS, RELOAD_NGINX
)
from scripts.commands import (
    copy_to_remote, get_image_hash, update_swarm,
    collect_static, upload_images, login_registry, build_images
)
from scripts.helpers import run_command, run_remote_commands, print_status, envsubst
from scripts.constants import (
    DEPLOY_DIR, PROD_APP_PATH, PROJECT_DOMAIN, COMPOSE_DIR,
    DOCKER_IMAGE_PREFIX, PROJECT_NAME, BASE_ENV_FILE, PROD_ENV_FILE, COMPOSE_PROFILES
)
from scripts.release import update_sentry_release
import os

def render_prod_nginx_conf(conf_name: str, target_name: str):
    envsubst(f'{DEPLOY_DIR}/nginx/conf/{conf_name}', f'{DEPLOY_DIR}/nginx/conf/{target_name}', ['PROJECT_NAME', 'PROJECT_DOMAIN'])
    copy_to_remote(f'{DEPLOY_DIR}/nginx/conf/{target_name}', f'/app/balancer/conf/{target_name}')
    run_command(f"rm {DEPLOY_DIR}/nginx/conf/{target_name}")



update_sentry_release()

collect_static()
build_images()
login_registry()
upload_images()

os.environ['DJANGO_IMAGE'] = get_image_hash(f'{DOCKER_IMAGE_PREFIX}-django')
os.environ['NEXTJS_IMAGE'] = get_image_hash(f'{DOCKER_IMAGE_PREFIX}-nextjs')

print_status(f"Deploying to {PROJECT_DOMAIN}")
run_remote_commands([f"mkdir -p {PROD_APP_PATH}", ])
print_status(f"Copying compose files to {PROJECT_DOMAIN}")

envsubst(f'{COMPOSE_DIR}/prod.yml.template', f'{COMPOSE_DIR}/prod.yml')
copy_to_remote(f'{COMPOSE_DIR}/prod.yml', f'{PROD_APP_PATH}/prod.yml')
run_command(f"rm {COMPOSE_DIR}/prod.yml")

copy_to_remote(f"{DEPLOY_DIR}/prod-scripts/certbot_renew.sh", "/etc/cron.daily")

print_status(f"Copying env files to {PROJECT_DOMAIN}")
copy_to_remote(BASE_ENV_FILE, f"{PROD_APP_PATH}/env.base")
copy_to_remote(PROD_ENV_FILE, f"{PROD_APP_PATH}/env")
run_remote_commands([INIT_SWARM_SCRIPT, PERFORM_MIGRATIONS])
update_swarm(f'{PROD_APP_PATH}/prod.yml', PROJECT_NAME)

print_status(f"Copying nginx config to {PROJECT_DOMAIN}")
render_prod_nginx_conf('nginx_prod.template', f'{PROJECT_NAME}.conf')
if "centrifugo" in COMPOSE_PROFILES:
    render_prod_nginx_conf('centrifugo_prod.template', f'{PROJECT_NAME}_centrifugo.conf')

print_status("Reloading nginx")
run_remote_commands([RELOAD_NGINX, ])