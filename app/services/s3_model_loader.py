import os
from pathlib import Path

import boto3


AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")


def download_s3_folder(bucket: str, prefix: str, local_dir: str) -> str:
    s3 = boto3.client("s3", region_name=AWS_REGION)
    local_path = Path(local_dir)
    local_path.mkdir(parents=True, exist_ok=True)

    normalized_prefix = prefix if prefix.endswith("/") else f"{prefix}/"
    paginator = s3.get_paginator("list_objects_v2")
    found_any = False

    for page in paginator.paginate(Bucket=bucket, Prefix=normalized_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            found_any = True
            relative_path = key[len(normalized_prefix):] if key.startswith(normalized_prefix) else key
            file_path = local_path / relative_path
            file_path.parent.mkdir(parents=True, exist_ok=True)

            if file_path.exists():
                print(f"[S3 Model Loader] Using cached local model file: {file_path}")
                continue

            print(f"[S3 Model Loader] Downloading: s3://{bucket}/{key} -> {file_path}")
            s3.download_file(bucket, key, str(file_path))

    if not found_any:
        raise RuntimeError(
            f"No model files found in s3://{bucket}/{normalized_prefix}. "
            "Check bucket/prefix and IAM read permissions."
        )

    return str(local_path)
