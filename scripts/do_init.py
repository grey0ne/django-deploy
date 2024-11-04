import time
from scripts.do_utils import (
    get_or_create_droplet, get_or_create_project, get_public_address,
    create_or_update_domain_record,
    get_or_create_pg_cluster, get_existing_pg_cluster,
    get_or_create_pg_user, get_or_create_pg_database, update_pg_firewall,
    DOException
)
from scripts.utils import save_env_option
from scripts.constants import PROJECT_DOMAIN, PROJECT_NAME
from scripts.do_constants import (
    DO_TOKEN, PROJECT_DESCRIPTION, DROPLET_NAME, PG_USERNAME,
    STATUS_CHECK_INTERVAL, PG_CLUSTER_NAME, PG_DB_NAME
)


REQUIRED_VARS: dict[str, str] = {
    'DO_TOKEN': DO_TOKEN,
    'PROJECT_NAME': PROJECT_NAME,
    'PROJECT_DOMAIN': PROJECT_DOMAIN,
    'DATABASE_USER': PG_USERNAME
}

def init_do_infra():
    for var_name, value in REQUIRED_VARS.items():
        if not value:
            print(f"{var_name} is not set")
            return
    project_data = get_or_create_project(PROJECT_NAME, PROJECT_DESCRIPTION)
    print(f"Using DO project {PROJECT_NAME} with id {project_data['id']}")
    droplet_data = get_or_create_droplet(DROPLET_NAME, project_data["id"])
    public_address = get_public_address(droplet_data)
    if public_address is None:
        raise DOException(f"Active droplet {DROPLET_NAME} doesn't have public address, aborting")
    print(f"Creating DNS record for droplet {DROPLET_NAME} with IP {public_address}")
    create_or_update_domain_record(PROJECT_DOMAIN, public_address)
    pg_cluster = get_or_create_pg_cluster(PG_CLUSTER_NAME, project_data["id"])
    cluster_status = pg_cluster['status']
    cluster_id = pg_cluster['id']
    save_env_option('DATABASE_HOST', pg_cluster['connection']['host'])
    while cluster_status == "creating":
        print(f"Postgres Cluster status is {cluster_status}. Cluster init could take up to 5 minutes")
        time.sleep(STATUS_CHECK_INTERVAL * 5)
        pg_cluster = get_existing_pg_cluster(PG_CLUSTER_NAME)
        if pg_cluster is not None:
            cluster_status = pg_cluster['status']
    pg_user = get_or_create_pg_user(cluster_id, PG_USERNAME)
    if 'password' in pg_user:
        save_env_option('DATABASE_PASSWORD', pg_user['password'])
    get_or_create_pg_database(cluster_id, PG_DB_NAME)
    update_pg_firewall(cluster_id, droplet_data['id'])


init_do_infra()