from django.conf import settings
from storages.backends.gcloud import GoogleCloudStorage
from storages.backends.s3boto3 import S3Boto3Storage


class S3MediaStorage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.AWS_MEDIA_BUCKET_NAME
        self.custom_domain = settings.AWS_MEDIA_CUSTOM_DOMAIN
        super().__init__(*args, **kwargs)


class GCSMediaStorage(GoogleCloudStorage):
    def __init__(self, *args, **kwargs):
        self.bucket_name = settings.GS_MEDIA_BUCKET_NAME
        super().__init__(*args, **kwargs)
