import hashlib
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

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


def calculate_checksum(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        checksum = hashlib.md5(data).hexdigest()
        return checksum


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
        2. It uploads files new or changed files (different checksum) to the S3 bucket and inserts them in the file cache.
        3. Any errors are logged
        4. If there were errors, a notification is sent to MS Teams
        """
        context.log.info(f"Backing up {self.name}")
        deleted: List[str] = []
        updated: List[Tuple[str, str]] = []
        added: List[Tuple[str, str]] = []
        errors: List[str] = []
        skipped: int = 0
        bucket: Optional[Bucket] = None
        for cached, _ in self.file_cache.list_all():
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
                    checksum = calculate_checksum(file)
                    if self.file_cache.is_new_or_changed(name, checksum):
                        if not context.dry_run:
                            if not bucket:
                                bucket = Bucket(self.name)
                            bucket.sync_file(name)
                        if self.file_cache.is_cached(name):
                            updated.append((name, checksum))
                        else:
                            added.append((name, checksum))
                    else:
                        skipped += 1
                except Exception as e:
                    message = f"Failed to backup *{safe_to_string(file)}*: `{e}`"
                    context.log.error(message)
                    errors.append(message)

        self.file_cache.upsert_all(added)
        self.file_cache.upsert_all(updated)
        self.file_cache.delete_all(deleted)
        log_entry = f"\t{len(added)} [new]\t{len(updated)} [updated]\t{len(deleted)} [deleted]\t{len(errors)} [errors]\t{skipped} [skipped]"
        if errors:
            context.log.error(f"Failure: {log_entry}")
            if context.notification_webhook:
                text = "\n".join(errors)
                message = pymsteams.connectorcard(context.notification_webhook)
                message.title(
                    f"Backup of '{self.name}' finished with {len(errors)} { 'error' if len(errors) == 1 else 'errors' }"
                )
                message.text(text)
                message.send()
        else:
            context.log.info(f"Success: {log_entry}")
            context.history.update(self.path, time.time())
