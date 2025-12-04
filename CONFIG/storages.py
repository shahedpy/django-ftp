"""CONFIG>storages.py"""

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class MediaStorage(S3Boto3Storage):
    """
    S3 storage for media files. Uses settings.AWS_LOCATION (e.g. 'sw_data')
    as `location` so uploaded keys are placed under that prefix.
    """
    location = getattr(settings, "AWS_LOCATION", "")
    default_acl = None
    file_overwrite = False
