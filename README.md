# django-ftp

Python: 3.14

```
python manage.py runserver [addr:port]
```

```
python manage.py ftpserver [addr:port]
```

## Using S3 for media storage

You can store uploaded files in an S3 bucket instead of the local `media/` directory. To enable S3-backed media storage, set these environment variables before running the app:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_STORAGE_BUCKET_NAME` (e.g. `dphe`)
- `AWS_S3_REGION_NAME` (optional)
- `AWS_S3_ENDPOINT_URL` (optional)

By default uploaded files will be stored under the `sw_data/` prefix in your S3 bucket (i.e. `s3://dphe/sw_data/`). You can override the prefix by setting `AWS_LOCATION`.

If `AWS_STORAGE_BUCKET_NAME` is not set, the project will fall back to local storage in `media/`.

Note: The `django-ftpserver` app in this project uses local filesystem storage, configured by `FTPSERVER_DIRECTORY` in `CONFIG/settings.py`. If you rely on the FTP service to receive uploads, those uploads will still land in `media/` (local) unless you adapt the FTP server to use a mounted S3 filesystem or a different backend. You can periodically migrate files to S3 using the migration script above.
To confirm uploads land under `sw_data` prefix, run:

```bash
aws s3 ls s3://dphe/sw_data/
```

You should see the files uploaded to that prefix similar to:
```
2025-11-24 16:14:25      18657 dp.jpg
2025-11-24 16:30:27       7132 dphe_logo.png
```


### Migrating existing files to S3

If you already have files in `media/` and want to copy them to your S3 bucket, use the provided script:

```bash
# copy into your venv python command if needed
/path/to/venv/bin/python scripts/migrate_media_to_s3.py --delete
```

This will upload files to the configured S3 bucket using the `DEFAULT_FILE_STORAGE`. Add `--delete` to remove the local copies after upload.

