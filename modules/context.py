import argparse
import json
import os
from typing import List, Optional, Tuple

import boto3
from mypy_boto3_s3.client import S3Client
from mypy_boto3_s3.literals import RegionName

from modules.logfile import Logfile

CONFIG_FILE_NAME = "config.json"
LOG_FILE_NAME = "backup.log"


class Context(object):
    """Parses the command line arguments and reads the config file to create the execution context."""

    _instance = None

    # Whether or not to perform a dry run; this means no data is uploaded to S3
    dry_run: bool = False

    # If true, the backup will reset the history file and file cache before running the backup
    reset: bool = False

    # Individual folders to be included as individual buckets
    folders: List[Tuple[str, str]] = []

    # The backup cache directory; config and other data will be stored here
    cache: str = ""

    log: Logfile

    aws_access_key: str = ""

    aws_secret_access_key: str = ""

    aws_region: RegionName = "eu-central-1"

    notification_webhook: Optional[str] = None

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
                "--reset",
                action="store_true",
                help="reset history and file cache",
            )
            parser.add_argument(
                "--cache",
                default="~/.local/matricula-backup/",
                help="where to store the config and cache files",
            )
            args = parser.parse_args()
            cls.cache = os.path.expanduser(args.cache)
            config_file = os.path.join(cls.cache, CONFIG_FILE_NAME)
            cls.log = Logfile(os.path.join(cls.cache, LOG_FILE_NAME))
            cls.dry_run = args.dry_run
            cls.reset = args.reset
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
                    cls.notification_webhook = config.get("notification", None).get(
                        "webhook", None
                    )
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
