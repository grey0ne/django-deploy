from scripts.constants import project_env
from scripts.nginx.templates import (
    NGINX_BASE_REDIRECT_TEMPLATE, HTTP_UPGRADE_TEMPLATE, NGINX_DEV_MEDIA_TEMPLATE,\
    NGINX_DEV_APP_TEMPLATE, CENTRIFUGO_DEV_TEMPLATE, NGINX_EXTRA_DEV_DOMAINS_TEMPLATE,
    APP_PROD_TEMPLATE, CENTRIFUGO_PROD_TEMPLATE, EXTRA_DOMAIN_PROD_TEMPLATE
)
from scripts.printing import print_status

def custom_format(template: str, **kwargs: str) -> str:
    for key, value in kwargs.items():
        template = template.replace(f"{{{key}}}", value)
    return template


def render_dev_nginx_conf(target_file: str):
    print_status(f"Generating dev nginx config to {target_file}")
    extra_domains_str = ' '.join(project_env.extra_domains) if len(project_env.extra_domains) > 0 else ''
    conf_str = \
f"""
{custom_format(NGINX_BASE_REDIRECT_TEMPLATE, PROJECT_DOMAIN=project_env.project_domain, EXTRA_DOMAINS=extra_domains_str)}
{HTTP_UPGRADE_TEMPLATE}
{custom_format(NGINX_DEV_MEDIA_TEMPLATE, PROJECT_NAME=project_env.project_name, PROJECT_DOMAIN=project_env.project_domain)}
{custom_format(NGINX_DEV_APP_TEMPLATE, PROJECT_DOMAIN=project_env.project_domain, PROJECT_NAME=project_env.project_name)}
"""

    with open(target_file, 'w') as f:
        f.write(conf_str)

def render_extra_dev_domain_nginx_conf(target_file: str, domain: str):
    print_status(f"Generating extra domain {domain} nginx config to {target_file}")
    conf_str = custom_format(NGINX_EXTRA_DEV_DOMAINS_TEMPLATE, DOMAIN=domain, PROJECT_NAME=project_env.project_name)

    with open(target_file, 'w') as f:
        f.write(conf_str)

def render_centrifugo_dev_nginx_conf(target_file: str):
    print_status(f"Generating dev centrifugo nginx config to {target_file}")
    conf_str = custom_format(CENTRIFUGO_DEV_TEMPLATE, PROJECT_NAME=project_env.project_name, PROJECT_DOMAIN=project_env.project_domain)

    with open(target_file, 'w') as f:
        f.write(conf_str)

def render_app_prod_nginx_conf(target_file: str):
    print_status(f"Generating prod nginx config to {target_file}")
    conf_str = custom_format(APP_PROD_TEMPLATE, PROJECT_NAME=project_env.project_name, PROJECT_DOMAIN=project_env.project_domain)

    with open(target_file, 'w') as f:
        f.write(conf_str)

def render_centrifugo_prod_nginx_conf(target_file: str):
    print_status(f"Generating prod centrifugo nginx config to {target_file}")
    conf_str = custom_format(CENTRIFUGO_PROD_TEMPLATE, PROJECT_NAME=project_env.project_name, PROJECT_DOMAIN=project_env.project_domain)

    with open(target_file, 'w') as f:
        f.write(conf_str)

def render_extra_domain_prod_nginx_conf(target_file: str, domain: str):
    print_status(f"Generating extra domain {domain} prod nginx config to {target_file}")
    conf_str = custom_format(EXTRA_DOMAIN_PROD_TEMPLATE, DOMAIN=domain, PROJECT_NAME=project_env.project_name)

    with open(target_file, 'w') as f:
        f.write(conf_str)