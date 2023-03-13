#!/usr/bin/env python3


from pathlib import Path

from modules.backup_location import BackupLocation
from modules.bucket import Bucket
from modules.context import Context

context = Context()

context.log.heading("Starting backup")

if context.dry_run:
    context.log.info("Performing dry run")

if context.reset:
    context.log.info("Resetting history and file cache")

# Back up all backup location folders
for name, path in context.folders:
    BackupLocation(name, path).backup()

# Back up the image cache
if not context.dry_run:
    bucket = Bucket("image-backup-cache", use_versioning=False)
    for file in Path(context.cache).rglob("*"):
        if file.is_file():
            bucket.sync_file(str(file), use_glacier=False)
    context.log.info("Synced backup cache")

context.log.heading("Finished backup")
