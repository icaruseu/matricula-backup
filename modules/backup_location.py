import time
from pathlib import Path
from typing import List

from modules.bucket import Bucket
from modules.context import Context
from modules.file_cache import FileCache

context = Context()


class BackupLocation:
    bucket: Bucket
    file_cache: FileCache
    name: str
    path: str

    def __init__(self, name: str, path: str):
        self.bucket = Bucket(name)
        self.file_cache = FileCache(name)
        self.name = name
        self.path = path

    def backup(self):
        context.log.info(f"Backing up {self.name}")
        deleted: List[str] = []
        updated: List[str] = []
        added: List[str] = []
        for cached in self.file_cache.list_all():
            if not Path(cached).is_file():
                deleted.append(cached)
                self.bucket.delete_file(cached)
        for file in Path(self.path).rglob("*"):
            if file.is_file():
                if file.stat().st_ctime > context.history.get_last_backup(self.path):
                    self.bucket.sync_file(file.as_posix())
                    if self.file_cache.is_cached(file.as_posix()):
                        updated.append(file.as_posix())
                    else:
                        added.append(file.as_posix())
        self.file_cache.insert_all(added)
        self.file_cache.delete_all(deleted)
        context.log.info(
            f"Result: {len(added)} [new]\t{len(updated)} [updated]\t{len(deleted)} [deleted]"
        )
        context.history.update(self.path, time.time())
