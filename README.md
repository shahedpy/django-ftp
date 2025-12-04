# django-ftp

Python: 3.14

This project includes a local FTP server that stores files under `media/`. You can also use AWS S3 for media storage instead of a local directory.

Quick start (local dev):

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py runserver
```

Start the FTP server (files written to `media/` by default):

```
python manage.py ftpserver [addr:port]
```

Note: By default the management command uses a non-privileged port (2121) to avoid permission errors on Unix systems. If you omit the `addr:port` argument and still see a permission error, it means the command is attempting to bind to a privileged port such as 21. Two options:

- Start on a non-privileged port using an explicit port: `python manage.py ftpserver 0.0.0.0:8080` or `2121`.
- Or update your Django settings to set `FTPSERVER_PORT` (e.g. `FTPSERVER_PORT = 2121`) so the command picks it up automatically.

Warning: Binding to ports below 1024 (like port 21) usually requires root privileges and is not recommended for local development.

Using AWS S3 for media storage
--------------------------------
1) Create an S3 bucket and choose a region.
2) Set your AWS credentials and bucket name in `CONFIG/local_settings.py` or using environment variables.
	- For local development you can copy `CONFIG/local_settings.example.py` to `CONFIG/local_settings.py` and update the values.
3) Ensure `django-storages` and `boto3` are installed (these are in `requirements.txt`).
4) Configure `AWS_STORAGE_BUCKET_NAME` in `CONFIG/settings.py` (or via `CONFIG/local_settings.py`). When a bucket is configured, this project will use S3 as the Django `DEFAULT_FILE_STORAGE`.
5) If you have existing files in `media/`, run the migration script to upload files to S3:

```
python scripts/migrate_media_to_s3.py --delete
```

Note: The FTP server still writes to the local `media/` directory. If you want users to upload files to S3 directly, consider disabling the FTP server and providing authenticated uploads using signed URLs or server-side proxies.

Security note: `CONFIG/local_settings.py` may contain AWS credentials. Do NOT commit real credentials to version control. If you already committed keys, rotate them immediately and remove the secrets from the repository's history.

