import subprocess
from subprocess import PIPE
from scripts.constants import PROJECT_DOMAIN, COMPOSE_DIR, DEPLOY_DIR
from scripts.commands import RELOAD_NGINX

def run_command(command: str):
    subprocess.run(command, shell=True, check=True)

def run_remote_commands(commands: list[str]):
    ssh_command = ['ssh', f'root@{PROJECT_DOMAIN}', "bash -s"]
    command = "\n".join(commands)
    p = subprocess.run(ssh_command, stdout=PIPE, input=command, encoding='ascii')
    if p.stdout:
        print(p.stdout)

def copy_to_remote(source: str, destination: str):
    run_command(f'scp {source} root@{PROJECT_DOMAIN}:{destination}')

def get_image_hash(image_name: str) -> str:
    command = ["docker", "inspect", "--format={{index .RepoDigests 0}}", image_name]
    p = subprocess.run(command, stdout=PIPE, encoding='ascii')
    if p.stdout:
        return p.stdout.strip()
    return ""

def print_status(msg: str):
    print(f"\033[0;32m{msg}\033[0m")

def reload_nginx():
    print_status("Reloading nginx")
    run_remote_commands([RELOAD_NGINX, ])

def update_swarm(compose_file: str, stack_name: str):
    print_status(f"Updating {stack_name} swarm")
    STACK_COMMAND = f"docker stack config -c {compose_file} | docker stack deploy --with-registry-auth --detach=false -c - {stack_name}"
    run_remote_commands([STACK_COMMAND, ])
    print_status("Prune images")
    run_remote_commands(['docker image prune -f',])

def setup_balancer():
    print_status("Copying balancer files")
    run_remote_commands([
        f"mkdir -p /app/balancer",
        f"mkdir -p /app/balancer/conf",
    ])
    copy_to_remote(f'{COMPOSE_DIR}/prod_balancer.yml', '/app/balancer/compose.yml')
    copy_to_remote(f'{DEPLOY_DIR}/nginx/conf/balancer.conf', '/app/balancer/conf/default.conf')
    update_swarm('/app/balancer/compose.yml', 'balancer')
    reload_nginx()

def envsubst(from_file: str, to_file: str, variables: list[str] = []):
    if variables:
        variables_str = f"'{",".join([f'${var}' for var in variables])}'"
    else:
        variables_str = ""
    run_command(f'envsubst {variables_str} < {from_file} > {to_file}')