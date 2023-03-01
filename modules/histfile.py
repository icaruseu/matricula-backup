import contextlib
import json
import os


class Histfile(contextlib.ExitStack):
    hist_file: str

    def __init__(self, hist_file: str):
        self.hist_file = hist_file

    def __read(self):
        try:
            with open(self.hist_file, "r") as f:
                return json.load(f)
        except:
            return {}

    def clear(self):
        try:
            os.remove(self.hist_file)
        except OSError:
            pass

    def update(self, folder: str, last_backup: float):
        data = self.__read()
        with open(self.hist_file, "w") as f:
            data[folder] = {"lastBackup": last_backup}
            f.write(json.dumps(data, indent=2))

    def get_last_backup(self, folder: str):
        return self.__read().get(folder, {}).get("lastBackup", 0)
