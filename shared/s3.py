from __future__ import annotations

import botocore.client
import botocore.session


def get_s3_client(
    aws_access_key_id: str,
    aws_secret_access_key: str,
    endpoint_url: str,
) -> botocore.client.BaseClient:
    return botocore.session.Session().create_client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        endpoint_url=endpoint_url,
    )


def ensure_s3_bucket_exists(s3: botocore.client.BaseClient, bucket_name: str) -> None:
    try:
        s3.head_bucket(Bucket=bucket_name)
    except botocore.client.ClientError:
        s3.create_bucket(Bucket=bucket_name)
