# Matricula Backup

This is a Python script intended to back up image folders on the Matricula Image
server to AWS S3 with the Deep Archive storage class.

## Configuration

The script relies on two configuration mechanisms, command line arguments and a
configuration file.

### Command line arguments

1. `--cache` specifies the cache directory. The configuration file is expected
   to reside here, the log and other files will also be created in this
   directory
2. `--reset` forces the script to reset the file cache
3. `--dry-run` disables upload to S3 and failure notification messages to MS
   Teams

### Configuration file

The script expects a `config.json` file located in the cache directory with the
following data:

```json
{
  "backup": {
    "folders": ["/folder/one", "/folder/two"],
    "roots": ["/root/folder/one", "/root/folder/two"]
  },
  "notification": {
    "webhook": "[MS Teams channel webhook URL]"
  },
  "aws": {
    "access_key": "[AWS IAM user access key]",
    "secret_access_key": "[AWS IAM user secret access key]"
  }
}
```

The meaning of the different fields is as follows:

- Backup `folders` are folders each considered to be a independent backup
  location. Each will be backed up to a separate bucket on S3.

- Backup `roots` are folders whose direct subfolders are each considered an
  individual backup folder. For instance, `/images/archives/` would be a root
  folder and its direct children `/images/archives/archive_1` and
  `/images/archives/archive_2` would be backed up in the same way as the
  individual entries in the `folders` config key, which means, `archive_1` and
  `archive_2` will be each uploaded as an independent backup to an separate
  bucket on S3.

- `notifications/webhook` is the URL of a MS Teams channel webhook where
  notifications about backup errors are sent to during each back-up run.

- `aws/access_key` and `aws/secret_access_key` are the credentials for an AWS
  IAM user that has permission to manage S3 buckets.

## Backup process

The `folders` and `roots` entries of the configuration file are transformed into
a list of folders, each representing the backup root of an independent backup to
a separate S3 bucket. This buckets are automatically created on the first item
upload. The buckets are versioning-enabled with an expiry time for non-current
versions after 180 days.

During the backup of each folder, all files are listed recursively and copied to
the backup's S3 bucket. The files are placed in the S3 _Deep Archive Storage
Class_ upon upload. The absolute file paths are used as S3 item keys so an
eventual restore to the original location is possible. This item key is stored
in a local backup cache along with the file modification time. On each
successive backup run, the local file cache is checked for files not existing
anymore so they can be deleted from the S3 bucket and the file system is checked
for new or updated files based on their modification time to upload to S3.

If the backup encounters any error during the backup process, a notification is
sent to the configured MS Teams channel.
