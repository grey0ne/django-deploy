import os
from typing import Any, Generator
import boto3 # type: ignore
from constants import (
    S3_MEDIA_BUCKET, S3_ACCESS_KEY_ID, S3_SECRET_KEY, S3_ENDPOINT_URL, S3_ACL,
    PROJECT_NAME
)
from mimetypes import guess_type
from printing import print_status

S3_BACKUP_PATH = '/tmp/s3_backup'



def get_s3_files_list(client: Any, dir: str, bucket: str, verbose: bool) -> Generator[str, None, None]:
    paginator = client.get_paginator('list_objects')
    counter = 0
    for result in paginator.paginate(Bucket=bucket, Delimiter='/', Prefix=dir):
        if result.get('CommonPrefixes') is not None:
            for subdir in result.get('CommonPrefixes'):
                for fl_key in get_s3_files_list(client, subdir.get('Prefix'), bucket, verbose):
                    yield fl_key
                    counter += 1
                    if verbose and counter % 100 == 0:
                        print(f'Found {counter} files')
        for fl in result.get('Contents', []):
            file_key = fl.get('Key')
            if not file_key.endswith('/'):
                yield fl.get('Key')
                counter += 1
                if verbose and counter % 100 == 0:
                    print(f'Found {counter} files')

def s3_create_bucket():
    client = get_client()
    media_bucket = S3_MEDIA_BUCKET or f'{PROJECT_NAME}-media'
    client.create_bucket(
        ACL=S3_ACL,
        Bucket=media_bucket
    )

def download_dir(client: Any, dir: str, local_dir: str, bucket: str, verbose: bool = True):
    print(f'Downloading Directory "{dir}" from bucket "{bucket}"')
    for file_key in get_s3_files_list(client, dir, bucket, verbose):
        dest_pathname = os.path.join(local_dir, file_key)
        if not os.path.exists(os.path.dirname(dest_pathname)):
            os.makedirs(os.path.dirname(dest_pathname))
        if os.path.exists(dest_pathname):
            print(f'Skipping file "{file_key}". Already exists')
            continue
        print(f'Downloading file "{file_key}"')
        client.download_file(bucket, file_key, dest_pathname)

def upload_dir(
    client: Any,
    dir: str, local_dir: str, bucket: str,
    verbose: bool = True, skip_existing: bool = True,
    file_type: str | None = None
):
    print_status(f'Uploading Directory "{local_dir}" to "{dir}" in bucket "{bucket}"')
    file_key_set: set[str] = set() 
    if skip_existing:
        for file_key in get_s3_files_list(client, dir, bucket, verbose):
            file_key_set.add(file_key)
        if verbose:
            print_status(f'Found {len(file_key_set)} files in S3')
    local_paths_list: list[tuple[str, str]] = []
    for root, _, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_dir)
            s3_path = os.path.join(dir, relative_path)
            local_paths_list.append((local_path, s3_path))
    total_files = len(local_paths_list)
    print_status(f'Found {total_files} local files')
    counter = 0
    for local_path, s3_path in local_paths_list:
        counter += 1
        if skip_existing and s3_path in file_key_set:
            if verbose:
                print(f'Skipping file "{s3_path}". Already exists in S3')
            continue
        if file_type is not None:
            if not local_path.endswith(file_type):
                if verbose:
                    print(f'Skipping file "{local_path}". Not a {file_type} file')
                continue
        mimetype = guess_type(local_path)[0]
        if verbose:
            print(f'{counter}/{total_files} Uploading {local_path} with type {mimetype} to {s3_path}')
        client.upload_file(
            local_path, bucket, s3_path, ExtraArgs={'ACL': S3_ACL, 'ContentType': mimetype}
        )


def get_client(verbose: bool = True) -> Any:
    endpoint_url = S3_ENDPOINT_URL or f'http://{PROJECT_NAME}-minio:9000'
    if verbose:
        print_status('Initiating S3 Client')
        print_status(f'S3 Endpoint {endpoint_url}')
        print_status(f'S3 Key ID {S3_ACCESS_KEY_ID}')
        print_status(f'ACL is {S3_ACL}')
    return boto3.client( # type: ignore
         service_name='s3',
         endpoint_url=endpoint_url,
         aws_access_key_id=S3_ACCESS_KEY_ID,
         aws_secret_access_key=S3_SECRET_KEY,
    )


def backup_s3(backup_path: str = S3_BACKUP_PATH):
    client = get_client()
    download_dir(client, '', os.path.join(backup_path, S3_MEDIA_BUCKET), S3_MEDIA_BUCKET)


def upload_s3(backup_path: str = S3_BACKUP_PATH, skip_existing: bool = True, verbose: bool = True, file_type: str | None = None):
    client = get_client(verbose=verbose)
    upload_dir(
        client=client, dir='', local_dir=os.path.join(backup_path, S3_MEDIA_BUCKET),
        bucket=S3_MEDIA_BUCKET, skip_existing=skip_existing, verbose=verbose, file_type=file_type
    )

