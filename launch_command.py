import sys
from dataclasses import dataclass
from scripts.helpers import print_status
from scripts.do_init import init_do_infra
from scripts.commands import (
    setup_balancer, update_dev_nginx, production_setup, create_s3_backup,
    restore_s3_backup, create_s3_dev_bucket
)
from scripts.deploy_production import deploy_production
from scripts.constants import ENV_DIR
from typing import Callable


@dataclass(kw_only=True, slots=True, frozen=True)
class Command:
    keywords: list[str]
    description: str
    func: Callable[[], None]

command = sys.argv[1]



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
    ),
    Command(
        keywords=["s3backupdev",],
        description="Download all files from Dev S3 to local directory",
        func=lambda: create_s3_backup(f"{ENV_DIR}/env.dev")
    ),
    Command(
        keywords=["s3restoredev",],
        description="Restores files from local backup to Dev S3",
        func=lambda: restore_s3_backup(f"{ENV_DIR}/env.dev")
    ),
    Command(
        keywords=["s3backupprod",],
        description="Download all files from Production S3 to local directory",
        func=lambda: create_s3_backup(f"{ENV_DIR}/env.prod")
    ),
    Command(
        keywords=["s3restoreprod",],
        description="Restores files from local backup to Production S3",
        func=lambda: restore_s3_backup(f"{ENV_DIR}/env.prod")
    ),
    Command(
        keywords=["s3createdevbucket",],
        description="Create S3 bucket for dev environment",
        func=create_s3_dev_bucket
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