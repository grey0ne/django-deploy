import sys
from dataclasses import dataclass
from scripts.helpers import run_remote_commands, print_status
from scripts.constants import COMPOSE_PROFILES
from scripts.shell_commands import SETUP_DOCKER, PROJECT_DOMAIN, GEN_FAKE_CERTS
from scripts.do_init import init_do_infra
from scripts.commands import setup_balancer, update_dev_nginx, setup_prod_domain_cert, reload_prod_nginx
from scripts.deploy_production import deploy_production
from typing import Any


@dataclass(kw_only=True, slots=True, frozen=True)
class Command:
    keywords: list[str]
    description: str
    func: Any

command = sys.argv[1]

def production_setup():
    print_status("Setting up docker")
    run_remote_commands([ SETUP_DOCKER, ])
    setup_balancer()
    print_status(f"Setting up certbot for domain {PROJECT_DOMAIN}")
    run_remote_commands([
        f"mkdir -p /app/certbot/certificates",
        f"mkdir -p /app/certbot/challenge",
    ])
    setup_prod_domain_cert(PROJECT_DOMAIN)
    if "centrifugo" in COMPOSE_PROFILES:
        setup_prod_domain_cert(f"centrifugo.{PROJECT_DOMAIN}")
    print_status(f"Copying fake certs to dummy folder")
    run_remote_commands([ GEN_FAKE_CERTS, ])
    reload_prod_nginx()

def list_commands():
    print_status("Available commands:")
    for command_data in COMMANDS:
        print(f"- {command_data.keywords[0]}: {command_data.description}")


COMMANDS: list[Command] = [
    Command(
        keywords=["prod_setup", "production_setup", "initprod"],
        description="Set up the production environment",
        func=production_setup
    ),
    Command(
        keywords=["initinfra",],
        description="Initialize the infrastructure on Digital Ocean",
        func=init_do_infra
    ),
    Command(
        keywords=["setup_balancer", "deploybalancer"],
        description="Set up the load balancer on Digital Ocean",
        func=setup_balancer
    ),
    Command(
        keywords=["update_dev_nginx",],
        description="Update the dev nginx balancer configuration",
        func=update_dev_nginx
    ),
    Command(
        keywords=["deploy", "deployprod"],
        description="Build and deploy the production environment",
        func=deploy_production
    )
]

COMMANDS_DICT: dict[str, Command] = {}

for command_data in COMMANDS:
    for keyword in command_data.keywords:
        if keyword in COMMANDS_DICT:
            raise ValueError(f"Duplicate command keyword. Improper configuration: {keyword}")
        COMMANDS_DICT[keyword] = command_data


if command in COMMANDS_DICT:
    COMMANDS_DICT[command].func()
else:
    print_status(f"Command '{command}' not found.")
    list_commands()