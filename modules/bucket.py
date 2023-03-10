import re
from typing import cast

from botocore.exceptions import ClientError
from mypy_boto3_s3.literals import BucketLocationConstraintType

from modules.context import Context

EXPIRATION_NONCURRENT_DAYS = 180
STORAGE_CLASS = "DEEP_ARCHIVE"

context = Context()


class Bucket:
    name: str

    def __init__(self, name: str, use_versioning: bool):
        name = re.sub(r"[^a-zA-Z0-9]", "-", name).lower()
        self.name = name
        # Create bucket if it doesn't exist
        try:
            context.s3_client.head_bucket(Bucket=name)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code", "-1") == "404":
                context.log.info(f"Creating bucket {name}")
                context.s3_client.create_bucket(
                    ACL="private",
                    Bucket=name,
                    CreateBucketConfiguration={
                        "LocationConstraint": cast(
                            BucketLocationConstraintType, context.aws_region
                        ),
                    },
                )
            else:
                raise error
        if use_versioning:
            # Set bucket versioning
            context.s3_client.put_bucket_versioning(
                Bucket=name,
                VersioningConfiguration={
                    "Status": "Enabled",
                },
            )
            # Set bucket lifecycle
            context.s3_client.put_bucket_lifecycle_configuration(
                Bucket=name,
                LifecycleConfiguration={
                    "Rules": [
                        {
                            "ID": "Delete_noncurrent_versions",
                            "Status": "Enabled",
                            "NoncurrentVersionExpiration": {
                                "NoncurrentDays": EXPIRATION_NONCURRENT_DAYS,
                            },
                            "Filter": {},
                        }
                    ]
                },
            )

    def __file_key(self, path: str) -> str:
        return path.lstrip("/")

    def sync_file(self, path: str, use_glacier: bool):
        if use_glacier:
            context.s3_client.upload_file(
                path,
                self.name,
                self.__file_key(path),
                ExtraArgs={"StorageClass": STORAGE_CLASS},
            )
        else:
            context.s3_client.upload_file(
                path,
                self.name,
                self.__file_key(path),
            )

    def delete_file(self, path: str):
        context.s3_client.delete_object(Bucket=self.name, Key=self.__file_key(path))
