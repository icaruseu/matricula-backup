#!/usr/bin/env python3


from modules.backup_location import BackupLocation
from modules.context import Context

context = Context()

context.log.heading("Starting backup")

if context.dry_run:
    context.log.info("Performing dry run")

if context.reset:
    context.log.info("Resetting history and file cache")
    context.history.clear()

for name, path in context.folders:
    BackupLocation(name, path).backup()

context.log.heading("Finished backup")
