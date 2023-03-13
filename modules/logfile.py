from datetime import datetime
from enum import Enum
from typing import Optional


class LogLevel(str, Enum):
    info = "INFO"
    warn = "WARN"
    err = "ERR"


class Logfile:
    log_file: str

    def __init__(self, log_file: str):
        self.log_file = log_file

    def __write(self, message: str, level: LogLevel = LogLevel.info):
        message = f"[{datetime.now()}] [{level}] {message}"
        print(message)
        with open(self.log_file, "a") as f:
            f.write(message + "\n")

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
