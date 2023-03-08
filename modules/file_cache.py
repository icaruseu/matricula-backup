import os
import sqlite3
import urllib.parse
from pathlib import Path
from typing import List, Tuple

from modules.context import Context

context = Context()


class FileCache:
    db_path: Path

    def __init__(self, name: str):
        file_name = urllib.parse.quote_plus(name) + ".db"
        parent = Path(context.home).joinpath("db")
        os.makedirs(parent, exist_ok=True)
        self.db_path = parent.joinpath(file_name)
        con = sqlite3.connect(self.db_path)
        con.cursor().execute(
            "CREATE TABLE IF NOT EXISTS files (key TEXT PRIMARY KEY, timestamp REAL);"
        )
        con.commit()
        con.close()

    def clear(self):
        con = sqlite3.connect(self.db_path)
        con.cursor().execute("DELETE FROM files;")
        con.commit()
        con.close()

    def upsert_all(self, files: List[Tuple[str, float]]):
        con = sqlite3.connect(self.db_path)
        cursor = con.cursor()
        for file_path, timestamp in files:
            cursor.execute(
                f"INSERT INTO files (key, timestamp) VALUES (:key, :timestamp) ON CONFLICT(key) DO UPDATE SET timestamp=:timestamp;",
                {"key": file_path, "timestamp": timestamp},
            )
        con.commit()
        con.close()

    def list_all(self) -> List[Tuple[str, float]]:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        cursor.execute("SELECT key, timestamp FROM files;")
        result = cursor.fetchall()
        con.close()
        return [(row["key"], row["timestamp"]) for row in result]

    def delete_all(self, file_paths: List[str]):
        con = sqlite3.connect(self.db_path)
        cursor = con.cursor()
        for file_path in file_paths:
            cursor.execute("DELETE FROM files WHERE key = :key;", {"key": file_path})
        con.commit()
        con.close()

    def is_cached(self, file_path: str) -> bool:
        con = sqlite3.connect(self.db_path)
        cursor = con.cursor()
        cursor.execute(
            "SELECT key FROM files WHERE key = :key;",
            {"key": file_path},
        )
        result = cursor.fetchall()
        con.close()
        return len(result) > 0

    def is_new_or_changed(self, file_path: str, timestamp: float) -> bool:
        con = sqlite3.connect(self.db_path)
        cursor = con.cursor()
        cursor.execute(
            "SELECT key FROM files WHERE key = :key AND ABS(timestamp - :timestamp) < 0.00001;",
            {"key": file_path, "timestamp": timestamp},
        )
        result = cursor.fetchall()
        con.close()
        return len(result) == 0
