import sys
from pathlib import Path
from typing import List, Optional

import pymsteams

from modules.bucket import Bucket
from modules.context import Context
from modules.file_cache import FileCache

BUCKET_PREFIX = "images--"
FILE_PROGRESS_LOG_THRESHOLD = 50000

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


def sizeof_fmt(size: float):
    """Converts a byte number to a human readable format

    Args:
        num The size of the file in byte: float

    Returns:
        String representation of the size
    """
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(size) < 1024.0:
            return f"{size:3.1f}{unit}B"
        size /= 1024.0
    return f"{size:.1f}YiB"


class BackupLocation:
    """Describes a backup location, including the AWS S3 bucket and file cache."""

    file_cache: FileCache
    bucket_name: str
    name: str
    path: str

    def __init__(self, name: str, path: str):
        self.file_cache = FileCache(name)
        self.name = name
        self.bucket_name = BUCKET_PREFIX + name
        self.path = path
        if context.reset:
            self.file_cache.clear()

    def backup(self):
        """Backs up the files in this location.
        1. It deletes files listed in the file cache but not on the file system anymore from the S3 bucket and file cacheself.
        2. It uploads files new or changed files based on their modification time to the S3 bucket and inserts them in the file cache.
        3. Any errors are logged
        4. If there were errors, a notification is sent to MS Teams
        """
        context.log.info(f"Backing up {self.name}")
        bucket: Optional[Bucket] = None
        errors: List[str] = []
        added_count: int = 0
        added_size: int = 0
        cached_count: int = 0
        deleted_count: int = 0
        skipped_count: int = 0
        total_count: int = 0
        total_size: int = 0
        updated_count: int = 0
        for cached, _ in self.file_cache.list_all():
            cached_count += 1
            if cached_count % FILE_PROGRESS_LOG_THRESHOLD == 0:
                print(f"\t{cached_count} cached files processed")
            if not Path(cached).is_file():
                if not context.dry_run:
                    if not bucket:
                        bucket = Bucket(self.bucket_name, use_versioning=True)
                    bucket.delete_file(cached)
                self.file_cache.delete_single(cached)
                deleted_count += 1
        for file in Path(self.path).rglob("*"):
            if file.is_file():
                total_count += 1
                if total_count % FILE_PROGRESS_LOG_THRESHOLD == 0:
                    print(f"\t{total_count} files processed")
                try:
                    total_size += file.stat().st_size
                    name = str(file)
                    timestamp = file.stat().st_mtime
                    if self.file_cache.is_new_or_changed(name, timestamp):
                        if not context.dry_run:
                            if not bucket:
                                bucket = Bucket(self.bucket_name, use_versioning=True)
                            bucket.sync_file(name, use_glacier=True)
                        self.file_cache.upsert_single((name, timestamp))
                        if self.file_cache.is_cached(name):
                            updated_count += 1
                        else:
                            added_count += 1
                            added_size += file.stat().st_size
                    else:
                        skipped_count += 1
                except Exception as e:
                    message = f"Failed to backup *{safe_to_string(file)}*: `{e}`"
                    context.log.error(message)
                    errors.append(message)
        log_entry = f"{added_count} ({sizeof_fmt(added_size)} of {sizeof_fmt(total_size)}) [new]; {updated_count} [updated]; {deleted_count} [deleted]; {len(errors)} [errors]; {skipped_count} [skipped]"
        if errors:
            context.log.error(f"Failure: {log_entry}")
            if context.notification_webhook and not context.dry_run:
                text = "\n".join(errors)
                message = pymsteams.connectorcard(context.notification_webhook)
                message.title(
                    f"Backup of '{self.name}' finished with {len(errors)} { 'error' if len(errors) == 1 else 'errors' }"
                )
                message.text(text)
                message.send()
        else:
            context.log.info(f"Success: {log_entry}")
