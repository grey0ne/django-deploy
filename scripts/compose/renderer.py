import os
from typing import Literal

from scripts.compose.services import (
    GENERATED_DIR,
    build_dev_balancer_compose,
    build_dev_compose,
    build_prod_balancer_compose,
    build_prod_compose,
)
from scripts.compose.yaml_dump import dump_yaml
from scripts.deploy_config import DeployConfig, get_deploy_config
from scripts.printing import print_status

ComposeTarget = Literal['dev', 'prod', 'dev_balancer', 'prod_balancer']


def _ensure_generated_dir() -> None:
    os.makedirs(GENERATED_DIR, exist_ok=True)


def _write_compose(filename: str, data: dict) -> str:
    _ensure_generated_dir()
    path = os.path.join(GENERATED_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(dump_yaml(data))
    return path


def render_dev_compose(config: DeployConfig | None = None) -> str:
    config = config or get_deploy_config()
    print_status(f'Rendering dev compose for {config.config_file_present and "deploy.json" or "defaults"}')
    return _write_compose('dev.yml', build_dev_compose(config))


def render_prod_compose(
    django_image: str,
    nextjs_image: str,
    config: DeployConfig | None = None,
) -> str:
    config = config or get_deploy_config()
    print_status(
        f'Rendering production compose (celery={config.celery_enabled}, '
        f'centrifugo={config.centrifugo_enabled})'
    )
    data = build_prod_compose(config, django_image, nextjs_image)
    return _write_compose('prod.yml', data)


def render_dev_balancer_compose() -> str:
    print_status('Rendering dev balancer compose')
    return _write_compose('dev_balancer.yml', build_dev_balancer_compose())


def render_prod_balancer_compose() -> str:
    print_status('Rendering prod balancer compose')
    return _write_compose('prod_balancer.yml', build_prod_balancer_compose())


def render_compose(target: ComposeTarget, **kwargs) -> str:
    if target == 'dev':
        return render_dev_compose(kwargs.get('config'))
    if target == 'prod':
        return render_prod_compose(
            kwargs['django_image'],
            kwargs['nextjs_image'],
            kwargs.get('config'),
        )
    if target == 'dev_balancer':
        return render_dev_balancer_compose()
    if target == 'prod_balancer':
        return render_prod_balancer_compose()
    raise ValueError(f'Unknown compose target: {target}')
