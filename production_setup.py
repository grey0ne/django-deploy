from scripts.helpers import run_remote_commands, print_status, setup_balancer
from scripts.commands import SETUP_CERTBOT, SETUP_DOCKER, PROJECT_DOMAIN, GEN_FAKE_CERTS

print_status("Setting up docker")
run_remote_commands([ SETUP_DOCKER, ])
setup_balancer()
print_status(f"Setting up certbot for domain {PROJECT_DOMAIN}")
run_remote_commands([
    f"mkdir -p /app/certbot/certificates",
    f"mkdir -p /app/certbot/challenge",
])
run_remote_commands([ SETUP_CERTBOT, ])
print_status(f"Copying fake certs to dummy folder")
run_remote_commands([ GEN_FAKE_CERTS, ])
