import json
import os
import warnings
from dataclasses import dataclass, field

from scripts.constants import PROJECT_DIR, project_env
from scripts.printing import print_status

DEPLOY_CONFIG_FILE = os.path.join(PROJECT_DIR, 'deploy.json')

DEFAULT_SERVICES = {
    'celery': False,
    'centrifugo': False,
}

DEFAULT_DEV = {
    'postgres': True,
    'minio': True,
}


@dataclass
class DeployConfig:
    celery_enabled: bool = False
    centrifugo_enabled: bool = False
    postgres_enabled: bool = True
    minio_enabled: bool = True
    django_worker_count: int = 2
    config_file_present: bool = False
    legacy_dev_optionals: bool = False

    def is_enabled(self, service: str) -> bool:
        return {
            'celery': self.celery_enabled,
            'centrifugo': self.centrifugo_enabled,
            'postgres': self.postgres_enabled,
            'minio': self.minio_enabled,
            'redis': self.needs_redis(),
        }.get(service, False)

    def needs_redis(self) -> bool:
        return self.celery_enabled or self.centrifugo_enabled

    def dev_includes_optional(self, service: str) -> bool:
        if self.legacy_dev_optionals and service in ('celery', 'centrifugo', 'redis'):
            return True
        if service == 'redis':
            return self.needs_redis()
        return self.is_enabled(service)


_deploy_config: DeployConfig | None = None


def _parse_bool(value, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes')
    return default


def _service_enabled(data: dict, name: str, default: bool) -> bool:
    services = data.get('services', {})
    entry = services.get(name, {})
    if isinstance(entry, bool):
        return entry
    if isinstance(entry, dict):
        return _parse_bool(entry.get('enabled'), default)
    return default


def _dev_enabled(data: dict, name: str, default: bool) -> bool:
    dev = data.get('dev', {})
    entry = dev.get(name, {})
    if isinstance(entry, bool):
        return entry
    if isinstance(entry, dict):
        return _parse_bool(entry.get('enabled'), default)
    return default


def _apply_compose_profiles_fallback(config: DeployConfig) -> DeployConfig:
    profiles = project_env.compose_profiles
    if not profiles:
        return config
    warnings.warn(
        'COMPOSE_PROFILES is deprecated; use deploy.json services.*.enabled instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    celery = config.celery_enabled or 'celery' in profiles
    centrifugo = config.centrifugo_enabled or 'centrifugo' in profiles
    return DeployConfig(
        celery_enabled=celery,
        centrifugo_enabled=centrifugo,
        postgres_enabled=config.postgres_enabled,
        minio_enabled=config.minio_enabled,
        django_worker_count=config.django_worker_count,
        config_file_present=config.config_file_present,
        legacy_dev_optionals=config.legacy_dev_optionals,
    )


def load_deploy_config() -> DeployConfig:
    global _deploy_config
    if _deploy_config is not None:
        return _deploy_config

    worker_count = 2
    try:
        worker_count = int(os.getenv('DJANGO_WORKER_COUNT', '2'))
    except ValueError:
        worker_count = 2

    if not os.path.isfile(DEPLOY_CONFIG_FILE):
        print_status('No deploy.json found; using legacy defaults')
        _deploy_config = _apply_compose_profiles_fallback(DeployConfig(
            celery_enabled=False,
            centrifugo_enabled=False,
            postgres_enabled=True,
            minio_enabled=True,
            django_worker_count=worker_count,
            config_file_present=False,
            legacy_dev_optionals=True,
        ))
        return _deploy_config

    with open(DEPLOY_CONFIG_FILE, encoding='utf-8') as f:
        data = json.load(f)

    django_section = data.get('django', {})
    if 'worker_count' in django_section:
        worker_count = int(django_section['worker_count'])

    config = DeployConfig(
        celery_enabled=_service_enabled(data, 'celery', DEFAULT_SERVICES['celery']),
        centrifugo_enabled=_service_enabled(data, 'centrifugo', DEFAULT_SERVICES['centrifugo']),
        postgres_enabled=_dev_enabled(data, 'postgres', DEFAULT_DEV['postgres']),
        minio_enabled=_dev_enabled(data, 'minio', DEFAULT_DEV['minio']),
        django_worker_count=worker_count,
        config_file_present=True,
        legacy_dev_optionals=False,
    )
    _deploy_config = _apply_compose_profiles_fallback(config)
    return _deploy_config


def get_deploy_config() -> DeployConfig:
    return load_deploy_config()


def reset_deploy_config() -> None:
    global _deploy_config
    _deploy_config = None
