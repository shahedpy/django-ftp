from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class MediaStorage(S3Boto3Storage):
    """Custom S3 storage class for media files.

    Uses the `AWS_STORAGE_BUCKET_NAME` and `AWS_LOCATION` settings from
    `CONFIG.settings` to store files under a common prefix inside the bucket.
    """
    bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    location = getattr(settings, 'AWS_LOCATION', '')
    file_overwrite = False
    default_acl = None
