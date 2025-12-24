from constants import project_env
from s3_utils import get_client, upload_dir

if __name__ == '__main__':
    client = get_client(verbose=False)
    upload_dir(client, '', '/app/src/collected_static', project_env.s3_static_bucket, verbose=False)