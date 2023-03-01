#!/usr/bin/env python3


from modules.backup_location import BackupLocation
from modules.context import Context

context = Context()

context.log.heading("Starting backup")

for name, path in context.folders:
    BackupLocation(name, path).backup()

context.log.heading("Finished backup")
