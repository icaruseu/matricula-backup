import sys
import time
from pathlib import Path
from typing import List, Optional

import pymsteams

from modules.bucket import Bucket
from modules.context import Context
from modules.file_cache import FileCache

context = Context()


def safe_to_string(path: Path) -> str:
    """Tries to convert a path to a string, replacing any invalid characters with a placeholder.

    Args:
        path: A file system path

    Returns:
        A string representation of the path
    """
    fse = sys.getfilesystemencoding()
    return str(path).encode(fse, "surrogateescape").decode("ISO-8859-1")


class BackupLocation:
    """Describes a backup location, including the AWS S3 bucket and file cache."""

    bucket: Bucket
    file_cache: FileCache
    name: str
    path: str

    def __init__(self, name: str, path: str):
        self.file_cache = FileCache(name)
        self.name = name
        self.path = path
        if context.reset:
            self.file_cache.clear()

    def backup(self):
        """Backs up the files in this location.
        1. It deletes files listed in the file cache but not on the file system anymore from the S3 bucket and file cacheself.
        2. It uploads files that have been modified since the last backup to the S3 bucket and inserts them in the file cache.
        3. Any errors are logged
        4. If there were errors, a notification is sent to MS Teams
        5. If there were no errors, the history file is updated
        """
        context.log.info(f"Backing up {self.name}")
        deleted: List[str] = []
        updated: List[str] = []
        added: List[str] = []
        errors: List[str] = []
        bucket: Optional[Bucket] = None
        for cached in self.file_cache.list_all():
            if not Path(cached).is_file():
                if not context.dry_run:
                    if not bucket:
                        bucket = Bucket(self.name)
                    bucket.delete_file(cached)
                deleted.append(cached)
        for file in Path(self.path).rglob("*"):
            if file.is_file():
                try:
                    name = str(file)
                    if file.stat().st_ctime > context.history.get_last_backup(
                        self.path
                    ):
                        if not context.dry_run:
                            if not bucket:
                                bucket = Bucket(self.name)
                            bucket.sync_file(name)
                        if self.file_cache.is_cached(name):
                            updated.append(name)
                        else:
                            added.append(name)
                except Exception as e:
                    message = f"Failed to backup {safe_to_string(file)}: {e}"
                    context.log.error(message)
                    errors.append(message)

        self.file_cache.insert_all(added)
        self.file_cache.delete_all(deleted)
        if errors:
            context.log.error(f"Result: {len(errors)} errors")
            if context.notification_webhook:
                text = "\n".join(errors)
                message = pymsteams.connectorcard(context.notification_webhook)
                message.title("Backup finished with errors")
                message.text(text)
                message.send()
        else:
            context.log.info(
                f"Result: {len(added)} [new]\t{len(updated)} [updated]\t{len(deleted)} [deleted]\t{len(errors)} [errors]"
            )
            context.history.update(self.path, time.time())
