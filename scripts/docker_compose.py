from constants import PROJECT_NAME

DJANGO_SERVICE: str = f"""
  ${PROJECT_NAME}-django:
    image: ${DJANGO_IMAGE}
    command: gunicorn -w ${DJANGO_WORKER_COUNT} -b 0.0.0.0:8000 -k application.worker.CustomUvicornWorker application.asgi
    networks:
      - prodnet
    env_file:
      - /app/${PROJECT_NAME}/env.base
      - /app/${PROJECT_NAME}/env
    volumes:
      - /app/${PROJECT_NAME}/backend_data:/app/backend_data
"""

NEXTJS_SERVICE: str = f"""
  ${PROJECT_NAME}-nextjs:
    image: ${NEXTJS_IMAGE}
    networks:
      - prodnet
    env_file:
      - /app/${PROJECT_NAME}/env.base
      - /app/${PROJECT_NAME}/env
"""

CELERY_SERVICE: str = f"""
  ${PROJECT_NAME}-celery:
    image: ${DJANGO_IMAGE}
    domainname: ${PROJECT_NAME}-celery
    container_name: ${PROJECT_NAME}-celery
    command: celery --app application.celeryapp worker -E -l info
    volumes:
      - /app/${PROJECT_NAME}/backend_data:/app/backend_data
    env_file:
      - /app/${PROJECT_NAME}/env.base
      - /app/${PROJECT_NAME}/env
    networks:
      - prodnet
"""

CENTRIFUGO_SERVICE: str = f"""
  ${PROJECT_NAME}-centrifugo:
    image: "centrifugo/centrifugo:v5.4.9"
    container_name: ${PROJECT_NAME}-centrifugo
    domainname: ${PROJECT_NAME}-centrifugo
    volumes:
      - ${PROJECT_DIR}/environment/centrifugo.json.dev:/centrifugo/centrifugo.json
    command: centrifugo -c centrifugo.json --engine=redis
    depends_on:
      - redis
    networks:
      - prodnet
"""

REDIS_SERVICE: str = f"""
  ${PROJECT_NAME}-redis:
    image: "redis:7.2.3"
    container_name: ${PROJECT_NAME}-redis
    domainname: ${PROJECT_NAME}-redis
    networks:
      - prodnet
"""


def render_production_compose_file():
    pass
