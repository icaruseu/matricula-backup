#!/usr/bin/env python3


from mypy_boto3_s3.literals import BucketLocationConstraintType

from modules.backup_location import BackupLocation
from modules.context import Context

context = Context()
log = context.log

context.log.heading("Starting backup")

for name, path in context.folders:
    BackupLocation(name, path).backup()


# print(context.s3_client.head_bucket(Bucket=folder))
# try:
# context.s3_client.create_bucket(
#     ACL="private",
#     Bucket=folder,
#     CreateBucketConfiguration={
#         "LocationConstraint": cast(
#             BucketLocationConstraintType, context.aws_region
#         )
#     },
# )
# except:
#     pass
# log.info(f"Backing up {folder} to vault {vault_name}")
# try:
#     client.describe_vault(vaultName=vault_name)
#     log.info(f"Opened vault {vault_name}")
# except client.exceptions.ResourceNotFoundException:
#     if not context.dry_run:
#         response = client.create_vault(vaultName=vault_name)
#     log.info(f"Created new vault {vault_name}")
# except Exception as e:
#     log.error("Stopped execution due to the following AWS exception: ", e)
#     exit(1)

# print(response)


context.log.heading("Finished backup")
