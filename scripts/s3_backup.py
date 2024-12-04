import os
from typing import Any, Generator
import boto3 # type: ignore
from constants import S3_MEDIA_BUCKET, S3_ACCESS_KEY_ID, S3_SECRET_KEY, S3_ENDPOINT_URL, S3_ACL

S3_BACKUP_PATH = '/tmp/s3_backup'

def get_s3_files_list(client: Any, dir: str, bucket: str) -> Generator[str, None, None]:
    paginator = client.get_paginator('list_objects')
    counter = 0
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=dir):
        if result.get('CommonPrefixes') is not None:
            for subdir in result.get('CommonPrefixes'):
                for fl_key in get_s3_files_list(client, subdir.get('Prefix'), bucket):
                    yield fl_key
                    counter += 1
                    if counter % 100 == 0:
                        print(f'Found {counter} files')
        for fl in result.get('Contents', []):
            file_key = fl.get('Key')
            if not file_key.endswith('/'):
                yield fl.get('Key')
                counter += 1
                if counter % 100 == 0:
                    print(f'Found {counter} files')


def download_dir(client: Any, dir: str, local_dir: str, bucket: str):
    print(f'Downloading Directory "{dir}" from bucket "{bucket}"')
    for file_key in get_s3_files_list(client, dir, bucket):
        dest_pathname = os.path.join(local_dir, file_key)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
        if os.path.exists(dest_pathname):
            print(f'Skipping file "{file_key}". Already exists')
            continue
        print(f'Downloading file "{file_key}"')
        client.download_file(bucket, file_key, dest_pathname)

def upload_dir(client: Any, dir: str, local_dir: str, bucket: str):
    print(f'Uploading Directory "{local_dir}" to "{dir}" in bucket "{bucket}"')
    file_key_set: set[str] = set() 
    for file_key in get_s3_files_list(client, dir, bucket):
        file_key_set.add(file_key)
    print(f'Found {len(file_key_set)} files in S3')
    local_paths_list: list[tuple[str, str]] = []
    for root, _, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_dir)
            s3_path = os.path.join(dir, relative_path)
            local_paths_list.append((local_path, s3_path))
    total_files = len(local_paths_list)
    print(f'Found {total_files} local files')
    counter = 0
    for local_path, s3_path in local_paths_list:
        counter += 1
        if s3_path in file_key_set:
            print(f'Skipping file "{s3_path}". Already exists')
            continue
        print(f'{counter}/{total_files} Uploading {local_path} to {s3_path}')
        client.upload_file(local_path, bucket, s3_path, ExtraArgs={'ACL': S3_ACL})


def get_client() -> Any:
    print('Initiating S3 Client')
    print(f'S3 Endpoint {S3_ENDPOINT_URL}')
    print(f'S3 Bucket {S3_MEDIA_BUCKET}') 
    print(f'S3 Key ID {S3_ACCESS_KEY_ID}')
    return boto3.client( # type: ignore
         service_name='s3',
         endpoint_url=S3_ENDPOINT_URL,
         aws_access_key_id=S3_ACCESS_KEY_ID,
         aws_secret_access_key=S3_SECRET_KEY,
    )


def backup_s3(backup_path: str = S3_BACKUP_PATH):
    if S3_MEDIA_BUCKET is None:
        raise ValueError(f'S3_MEDIA_BUCKET is None')
    client = get_client()
    download_dir(client, '', os.path.join(backup_path, S3_MEDIA_BUCKET), S3_MEDIA_BUCKET)

def upload_s3(backup_path: str = S3_BACKUP_PATH):
    if S3_MEDIA_BUCKET is None:
        raise ValueError(f'S3_MEDIA_BUCKET is None')
    client = get_client()
    upload_dir(client, '', os.path.join(backup_path, S3_MEDIA_BUCKET), S3_MEDIA_BUCKET)

if __name__ == '__main__':
    backup_s3()