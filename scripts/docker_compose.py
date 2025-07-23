from scripts.constants import PROJECT_NAME, DEPLOY_DIR
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
    image: "centrifugo/centrifugo:v5.4.9"
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
    image: "redis:7.2.3"
    networks:
      - prodnet
"""


def render_production_compose_file(django_image: str, nextjs_image: str, django_worker_count: int = 2) -> None:
    compose_content = f"""
services:
{DJANGO_SERVICE.format(PROJECT_NAME=PROJECT_NAME, DJANGO_IMAGE=django_image, DJANGO_WORKER_COUNT=django_worker_count)}
{NEXTJS_SERVICE.format(PROJECT_NAME=PROJECT_NAME, NEXTJS_IMAGE=nextjs_image)}
{CELERY_SERVICE.format(PROJECT_NAME=PROJECT_NAME, DJANGO_IMAGE=django_image)}
{CENTRIFUGO_SERVICE.format(PROJECT_NAME=PROJECT_NAME)}
{REDIS_SERVICE.format(PROJECT_NAME=PROJECT_NAME)}
networks:
  prodnet:
    name: prodnet
    external: true
"""
    with open(os.path.join(DEPLOY_DIR, 'compose', 'prod.yml'), 'w') as f:
        f.write(compose_content)