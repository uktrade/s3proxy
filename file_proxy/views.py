import boto3

from django.conf import settings
from django.http import StreamingHttpResponse


s3 = boto3.client("s3")


def file_proxy(request, s3_path):
    s3_file = s3.get_object(
        Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        Key=s3_path,
    )

    return StreamingHttpResponse(
        s3_file["Body"].iter_chunks(chunk_size=settings.CHUNK_SIZE),
        content_type=s3_file["ContentType"],
    )
