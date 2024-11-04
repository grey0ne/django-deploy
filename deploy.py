from scripts.commands import (
    INIT_SWARM_SCRIPT, PERFORM_MIGRATIONS, COLLECT_STATIC_SCRIPT,
    BUILD_IMAGES_SCRIPT, RELOAD_NGINX
)
from scripts.helpers import (
    run_command, run_remote_commands, copy_to_remote, print_status, get_image_hash, update_swarm,
    envsubst
)
from scripts.constants import (
    DEPLOY_DIR, PROD_APP_PATH, PROJECT_DOMAIN, COMPOSE_DIR, DOCKER_IMAGE_PREFIX, PROJECT_NAME, BASE_ENV_FILE, PROD_ENV_FILE
)
from scripts.release import update_sentry_release
import os



update_sentry_release()

run_command(COLLECT_STATIC_SCRIPT)
run_command(BUILD_IMAGES_SCRIPT)

os.environ['DJANGO_IMAGE'] = get_image_hash(f'{DOCKER_IMAGE_PREFIX}-django')
os.environ['NEXTJS_IMAGE'] = get_image_hash(f'{DOCKER_IMAGE_PREFIX}-nextjs')


print_status(f"Deploying to {PROJECT_DOMAIN}")
run_remote_commands([f"mkdir -p {PROD_APP_PATH}", ])
print_status(f"Copiyng compose files to {PROJECT_DOMAIN}")

envsubst(f'{COMPOSE_DIR}/prod.yml.template', f'{COMPOSE_DIR}/prod.yml')
copy_to_remote(f'{COMPOSE_DIR}/prod.yml', f'{PROD_APP_PATH}/prod.yml')
run_command(f"rm {COMPOSE_DIR}/prod.yml")

copy_to_remote(f"{DEPLOY_DIR}/prod-scripts/certbot_renew.sh", "/etc/cron.daily")

print_status(f"Copiyng env files to {PROJECT_DOMAIN}")
copy_to_remote(BASE_ENV_FILE, f"{PROD_APP_PATH}/env.base")
copy_to_remote(PROD_ENV_FILE, f"{PROD_APP_PATH}/env")
run_remote_commands([INIT_SWARM_SCRIPT, PERFORM_MIGRATIONS])
update_swarm(f'{PROD_APP_PATH}/prod.yml', PROJECT_NAME)

print_status(f"Copiyng nginx config to {PROJECT_DOMAIN}")
envsubst(f'{DEPLOY_DIR}/nginx/conf/nginx_prod.template', f'{DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}.conf', ['PROJECT_NAME', 'PROJECT_DOMAIN'])
copy_to_remote(f'{DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}.conf', f'/app/balancer/conf/{PROJECT_NAME}.conf')
run_command(f"rm {DEPLOY_DIR}/nginx/conf/{PROJECT_NAME}.conf")

print_status("Reloading nginx")
run_remote_commands([RELOAD_NGINX, ])