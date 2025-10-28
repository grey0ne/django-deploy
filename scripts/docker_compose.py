from scripts.constants import PROJECT_NAME, DEPLOY_DIR, COMPOSE_PROFILES
from scripts.printing import print_status
import os

DJANGO_SERVICE: str = \
"""  {PROJECT_NAME}-django:
    image: {DJANGO_IMAGE}
    command: gunicorn -w {DJANGO_WORKER_COUNT} -b 0.0.0.0:8000 -k application.worker.CustomUvicornWorker application.asgi
    networks:
      - prodnet
    env_file:
      - /app/{PROJECT_NAME}/env.base
      - /app/{PROJECT_NAME}/env
    volumes:
      - /app/{PROJECT_NAME}/backend_data:/app/backend_data
"""

NEXTJS_SERVICE: str = \
"""  {PROJECT_NAME}-nextjs:
    image: {NEXTJS_IMAGE}
    networks:
      - prodnet
    env_file:
      - /app/{PROJECT_NAME}/env.base
      - /app/{PROJECT_NAME}/env
"""

CELERY_SERVICE: str = \
"""  {PROJECT_NAME}-celery:
    image: {DJANGO_IMAGE}
    command: celery --app application.celeryapp worker -E -l info
    volumes:
      - /app/{PROJECT_NAME}/backend_data:/app/backend_data
    env_file:
      - /app/{PROJECT_NAME}/env.base
      - /app/{PROJECT_NAME}/env
    networks:
      - prodnet
"""

CENTRIFUGO_SERVICE: str = \
"""  {PROJECT_NAME}-centrifugo:
    image: "centrifugo/centrifugo:v6.2"
    command: centrifugo
    env_file:
      - /app/{PROJECT_NAME}/env.base
      - /app/{PROJECT_NAME}/env
    depends_on:
      - redis
    networks:
      - prodnet
"""

REDIS_SERVICE: str = \
"""  {PROJECT_NAME}-redis:
    image: "redis:8.2.2-alpine"
    networks:
      - prodnet
"""

NETWORK_CONFIG: str = \
"""
networks:
  prodnet:
    name: prodnet
    external: true
"""

def render_production_compose_file(django_image: str, nextjs_image: str, django_worker_count: int = 2) -> None:
    print_status(f"Rendering production compose file for {PROJECT_NAME} with profiles {COMPOSE_PROFILES}")

    compose_content = "services:\n"
    compose_content += f"{DJANGO_SERVICE.format(PROJECT_NAME=PROJECT_NAME, DJANGO_IMAGE=django_image, DJANGO_WORKER_COUNT=django_worker_count)}\n"
    compose_content += f"{NEXTJS_SERVICE.format(PROJECT_NAME=PROJECT_NAME, NEXTJS_IMAGE=nextjs_image)}\n"

    if 'celery' in COMPOSE_PROFILES:
        compose_content += f"{CELERY_SERVICE.format(PROJECT_NAME=PROJECT_NAME, DJANGO_IMAGE=django_image)}\n"
    if 'centrifugo' in COMPOSE_PROFILES:
        compose_content+=f"{CENTRIFUGO_SERVICE.format(PROJECT_NAME=PROJECT_NAME)}\n"
    if 'celery' in COMPOSE_PROFILES or 'centrifugo' in COMPOSE_PROFILES:
        compose_content+=f"{REDIS_SERVICE.format(PROJECT_NAME=PROJECT_NAME)}\n"

    compose_content+=NETWORK_CONFIG
    with open(os.path.join(DEPLOY_DIR, 'compose', 'prod.yml'), 'w') as f:
        f.write(compose_content)