#!/usr/bin/env python3
"""
Simple script to copy files from local MEDIA_ROOT into configured DEFAULT_FILE_STORAGE.

Ensure the following before running:
  - Your virtualenv is activated (`venv/bin/activate` or use the venv python executable)
  - `AWS_STORAGE_BUCKET_NAME` is set and `DEFAULT_FILE_STORAGE` is configured to S3 storage

Usage:
  /path/to/venv/bin/python scripts/migrate_media_to_s3.py --delete
  (add --delete to remove local files after successful upload)
"""
import argparse
import os
import sys
from pathlib import Path

if __name__ == '__main__':
    sys.path.append(str(Path(__file__).resolve().parents[1]))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CONFIG.settings')

    import django
    django.setup()

    from django.conf import settings
    from django.core.files.storage import default_storage

    parser = argparse.ArgumentParser(description='Migrate local MEDIA files to default storage')
    parser.add_argument('--delete', action='store_true', help='Delete local files after successful upload')
    args = parser.parse_args()

    media_root = Path(settings.MEDIA_ROOT)
    if not media_root.exists():
        print('MEDIA_ROOT does not exist:', media_root)
        sys.exit(1)

    print('Starting migration from', media_root, 'to default storage')
    for root, dirs, files in os.walk(media_root):
        for f in files:
            full_path = Path(root) / f
            rel_path = full_path.relative_to(media_root)
            storage_path = str(rel_path).replace('\\', '/')
            from django.core.files.base import ContentFile
            with open(full_path, 'rb') as fh:
                content = fh.read()
            if default_storage.exists(storage_path):
                print('Already exists in storage, skipping:', storage_path)
                continue
            print('Uploading', storage_path)
            default_storage.save(storage_path, ContentFile(content))
            if args.delete:
                print('Deleting local file', full_path)
                full_path.unlink()

    print('Migration complete')
