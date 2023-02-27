import contextlib
from datetime import datetime
from enum import Enum
from io import TextIOWrapper
from typing import Optional


class LogLevel(str, Enum):
    info = "INFO"
    warn = "WARN"
    err = "ERR"


class Logfile(contextlib.ExitStack):
    log_file: TextIOWrapper

    def __init__(self, log_file: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log_file = self.enter_context(open(log_file, "a"))

    def __write(self, message: str, level: LogLevel = LogLevel.info):
        message = f"[{datetime.now()}] [{level}] {message}"
        print(message)
        self.log_file.write(message + "\n")

    def newline(self):
        self.info("\n")

    def heading(self, message: str):
        self.info("")
        self.info("*************************")
        self.info(message)
        self.info("*************************")
        self.info("")

    def info(self, message: str):
        self.__write(message, LogLevel.info)

    def error(self, message: str, error: Optional[Exception] = None):
        message = f"{message}: {error}" if error else message
        self.__write(message, LogLevel.err)

    def warn(self, message: str):
        self.__write(message, LogLevel.warn)
