from subprocess import PIPE
import subprocess
import fileinput

from scripts.constants import PROJECT_DOMAIN, PROD_ENV_FILE


def save_env_option(option_name: str, value: str, env_file: str = PROD_ENV_FILE, create: bool = False):
    option_found = False
    with fileinput.input(files=(env_file, ), encoding="utf-8", inplace=True) as f:
        for line in f:
            if f'{option_name}=' in line:
                result = f'{option_name}={value}\n'
                option_found=True
            else:
                result = line
            print(result, end='')
        if not option_found:
            if create:
                print(f'{option_name}={value}\n', end='')
            else:
                raise Exception('Option not found')

def run_command(command: str):
    subprocess.run(command, shell=True, check=True)

def run_remote_commands(commands: list[str]):
    ssh_command = ['ssh', f'root@{PROJECT_DOMAIN}', "bash -s"]
    command = "\n".join(commands)
    p = subprocess.run(ssh_command, stdout=PIPE, input=command, encoding='ascii')
    if p.stdout:
        print(p.stdout)

def print_status(msg: str):
    print(f"\033[0;32m{msg}\033[0m")


def envsubst(from_file: str, to_file: str, variables: list[str] = []):
    if variables:
        variables_str = f"'{",".join([f'${var}' for var in variables])}'"
    else:
        variables_str = ""
    run_command(f'envsubst {variables_str} < {from_file} > {to_file}')
