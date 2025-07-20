from constants import S3_STATIC_BUCKET
from s3_utils import get_client, upload_dir

if __name__ == '__main__':
    client = get_client(verbose=False)
    upload_dir(client, '', '/app/src/collected_static', S3_STATIC_BUCKET, verbose=False)