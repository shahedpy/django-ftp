from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """S3 storage for user-uploaded files.

    Location is set via the `AWS_LOCATION` setting (defaults to 'sw_data').
    """

    bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
    location = getattr(settings, 'AWS_LOCATION', 'sw_data')
    default_acl = None
    file_overwrite = False
