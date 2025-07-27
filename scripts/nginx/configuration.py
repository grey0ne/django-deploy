from scripts.constants import PROJECT_DOMAIN, PROJECT_NAME, EXTRA_DOMAINS
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
    extra_domains_str = ' '.join(EXTRA_DOMAINS) if len(EXTRA_DOMAINS) > 0 else ''
    conf_str = \
f"""
{custom_format(NGINX_BASE_REDIRECT_TEMPLATE, PROJECT_DOMAIN=PROJECT_DOMAIN, EXTRA_DOMAINS=extra_domains_str)}
{HTTP_UPGRADE_TEMPLATE}
{custom_format(NGINX_DEV_MEDIA_TEMPLATE, PROJECT_NAME=PROJECT_NAME, PROJECT_DOMAIN=PROJECT_DOMAIN)}
{custom_format(NGINX_DEV_APP_TEMPLATE, PROJECT_DOMAIN=PROJECT_DOMAIN, PROJECT_NAME=PROJECT_NAME)}
"""

    with open(target_file, 'w') as f:
        f.write(conf_str)

def render_extra_dev_domain_nginx_conf(target_file: str, domain: str):
    print_status(f"Generating extra domain {domain} nginx config to {target_file}")
    conf_str = custom_format(NGINX_EXTRA_DEV_DOMAINS_TEMPLATE, DOMAIN=domain, PROJECT_NAME=PROJECT_NAME)

    with open(target_file, 'w') as f:
        f.write(conf_str)

def render_centrifugo_dev_nginx_conf(target_file: str):
    print_status(f"Generating dev centrifugo nginx config to {target_file}")
    conf_str = custom_format(CENTRIFUGO_DEV_TEMPLATE, PROJECT_NAME=PROJECT_NAME, PROJECT_DOMAIN=PROJECT_DOMAIN)

    with open(target_file, 'w') as f:
        f.write(conf_str)

def render_app_prod_nginx_conf(target_file: str):
    print_status(f"Generating prod nginx config to {target_file}")
    conf_str = custom_format(APP_PROD_TEMPLATE, PROJECT_NAME=PROJECT_NAME, PROJECT_DOMAIN=PROJECT_DOMAIN)

    with open(target_file, 'w') as f:
        f.write(conf_str)

def render_centrifugo_prod_nginx_conf(target_file: str):
    print_status(f"Generating prod centrifugo nginx config to {target_file}")
    conf_str = custom_format(CENTRIFUGO_PROD_TEMPLATE, PROJECT_NAME=PROJECT_NAME, PROJECT_DOMAIN=PROJECT_DOMAIN)

    with open(target_file, 'w') as f:
        f.write(conf_str)

def render_extra_domain_prod_nginx_conf(target_file: str, domain: str):
    print_status(f"Generating extra domain {domain} prod nginx config to {target_file}")
    conf_str = custom_format(EXTRA_DOMAIN_PROD_TEMPLATE, DOMAIN=domain, PROJECT_NAME=PROJECT_NAME)

    with open(target_file, 'w') as f:
        f.write(conf_str)