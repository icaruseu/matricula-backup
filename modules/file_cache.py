import os
import sqlite3
import urllib.parse
from pathlib import Path
from typing import List

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
        con.cursor().execute("CREATE TABLE IF NOT EXISTS files (key TEXT PRIMARY KEY);")
        con.commit()
        con.close()

    def insert_all(self, file_paths: List[str]):
        con = sqlite3.connect(self.db_path)
        cursor = con.cursor()
        for file_path in file_paths:
            cursor.execute(
                f"INSERT OR IGNORE INTO files (key) VALUES (?);", (file_path,)
            )
        con.commit()
        con.close()

    def list_all(self) -> List[str]:
        con = sqlite3.connect(self.db_path)
        cursor = con.cursor()
        cursor.execute("SELECT key FROM files;")
        result = cursor.fetchall()
        con.close()
        return [row[0] for row in result]

    def delete_all(self, file_paths: List[str]):
        con = sqlite3.connect(self.db_path)
        cursor = con.cursor()
        for file_path in file_paths:
            cursor.execute("DELETE FROM files WHERE key = ?;", (file_path,))
        con.commit()
        con.close()

    def is_cached(self, file_path: str) -> bool:
        con = sqlite3.connect(self.db_path)
        cursor = con.cursor()
        cursor.execute("SELECT key FROM files WHERE key = ?;", (file_path,))
        result = cursor.fetchall()
        con.close()
        return len(result) > 0
