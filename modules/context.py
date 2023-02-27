import argparse
import json
import os
from typing import List, Tuple

import boto3
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.literals import RegionName

from modules.histfile import Histfile
from modules.logfile import Logfile

config_file_name = "config.json"
history_file_name = "history.json"
log_file_name = "backup.log"


class Context(object):
    """Parses the command line arguments and reads the config file to create the execution context."""

    _instance = None

    # Whether or not to perform a dry run
    dry_run: bool = False

    # Individual folders to be included as individual buckets
    folders: List[Tuple[str, str]] = []

    # The backup home directory
    home: str = ""

    # The log object
    log: Logfile

    history: Histfile

    # The AWS access key
    aws_access_key: str = ""

    # The AWS secret key
    aws_secret_access_key: str = ""

    # The AWS region
    aws_region: RegionName = "eu-central-1"

    s3_client: S3Client

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Context, cls).__new__(cls)
            # Parse command line arguments
            parser = argparse.ArgumentParser(
                prog="Matricula Sync",
                description="Syncs image folders with aws s3 glacier.",
            )
            parser.add_argument(
                "--dry-run",
                action="store_true",
                help="perform a trial run with no changes made",
            )
            parser.add_argument(
                "--home",
                default="~/.local/matricula-backup/",
                help="where to store the config and cache files",
            )
            args = parser.parse_args()
            cls.home = os.path.expanduser(args.home)
            config_file = os.path.join(cls.home, config_file_name)
            cls.log = Logfile(os.path.join(cls.home, log_file_name))
            cls.history = Histfile(os.path.join(cls.home, history_file_name))
            cls.dry_run = args.dry_run
            # Read config file
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                    cls.aws_access_key = config["aws"]["access_key"]
                    cls.aws_secret_access_key = config["aws"]["secret_access_key"]
                    cls.aws_region = config["aws"].get("region", cls.aws_region)
                    folders = [
                        os.path.expanduser(folder)
                        for folder in config["backup"].get("folders", [])
                    ]
                    for root_name in config["backup"].get("roots", []):
                        for folder_name in os.listdir(root_name):
                            folders.append(
                                os.path.expanduser(os.path.join(root_name, folder_name))
                            )
                    folders.sort()
                    common = os.path.commonpath(folders)
                    cls.folders = [
                        (
                            os.path.relpath(folder, common),
                            folder,
                        )
                        for folder in folders
                    ]
            except FileNotFoundError:
                print(f"Error reading config file: '{args.config_file}'")
                exit(1)
            except KeyError as e:
                print(f"Error parsing config file: missing key {e}")
                exit(1)
            except Exception as e:
                print(f"Error: {e}")
                exit(1)

            cls.s3_client = boto3.client(
                "s3",
                aws_access_key_id=cls.aws_access_key,
                aws_secret_access_key=cls.aws_secret_access_key,
                region_name=cls.aws_region,
            )
        return cls._instance
