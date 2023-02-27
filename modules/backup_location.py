import time
from pathlib import Path
from typing import List

from modules.context import Context
from modules.file_cache import FileCache

context = Context()


class BackupLocation:
    path: str
    file_cache: FileCache
    name: str

    def __init__(self, name: str, path: str):
        self.file_cache = FileCache(name)
        self.name = name
        self.path = path

    def backup(self):
        deleted: List[str] = []
        updated: List[str] = []
        added: List[str] = []
        for cached in self.file_cache.list_all():
            if not Path(cached).is_file():
                deleted.append(cached)
                # TODO: Delete file in s3
        for file in Path(self.path).rglob("*"):
            if file.is_file():
                if file.stat().st_ctime > context.history.get_last_backup(self.path):
                    # TODO: Upload file to s3
                    if self.file_cache.is_cached(file.as_posix()):
                        updated.append(file.as_posix())
                    else:
                        added.append(file.as_posix())
        self.file_cache.insert_all(added)
        self.file_cache.delete_all(deleted)
        context.log.info(
            f"Backed up {self.name}; new: {len(added)}; updated: {len(updated)}; deleted: {len(deleted)}"
        )
        context.history.update(self.path, time.time())

    def restore(self):
        # TODO: Download all files listed in the cache
        pass
