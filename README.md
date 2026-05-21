# django-deploy

Scripts for automating deploy of django + nextjs based projects.

This repo is expected to be a **git submodule** at `deploy/` in the project repo. The project root should contain `backend/`, `spa/`, `deploy/`, `environment/`, and **`deploy.json`**.

## Configuration

| Location | Purpose |
|----------|---------|
| `deploy.json` (project root) | Non-secret deploy toggles: optional services, gunicorn workers, dev-only services |
| `environment/env.base` | Shared project settings (`PROJECT_NAME`, registry, domains) |
| `environment/env.dev` | Development secrets and overrides |
| `environment/env.prod` | Production secrets |

### deploy.json example

```json
{
  "services": {
    "celery": { "enabled": false },
    "centrifugo": { "enabled": false }
  },
  "dev": {
    "postgres": { "enabled": true },
    "minio": { "enabled": true }
  },
  "django": {
    "worker_count": 2
  }
}
```

- **services**: optional production (and dev) stack pieces. `redis` is added automatically when celery or centrifugo is enabled.
- **dev**: local-only services (`postgres`, `minio`).
- **django.worker_count**: gunicorn workers in production (falls back to `DJANGO_WORKER_COUNT` in `env.base` when omitted).

If `deploy.json` is missing, dev compose includes celery/centrifugo/redis with compose **profiles** (legacy template behavior). Production includes only django and nextjs unless `COMPOSE_PROFILES` is set (deprecated; use `deploy.json`).

## Docker Compose generation

Compose files are generated under `deploy/compose/generated/` (gitignored). Regeneration runs automatically when using `./deploy/dc` or `pc`.

Manual generation:

```bash
./deploy/dc generate_compose
# or
python3 deploy/launch_command.py generate_compose  # with env.base + env.dev loaded
```

Production `prod.yml` is generated during `deployprod` and copied to the server (ephemeral local copy under `deploy/compose/`).

## Project layout

Backend dependencies are installed via `install-dependencies.sh` in the backend folder.
