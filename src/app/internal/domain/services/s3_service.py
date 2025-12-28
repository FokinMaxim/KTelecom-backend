import os
import boto3
import uuid
from dotenv import load_dotenv

load_dotenv()
S3_REGION = os.getenv("S3_REGION")
S3_ENDPOINT = os.getenv("S3_ENDPOINT")
S3_BUCKET = os.getenv("S3_BUCKET")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


class S3StorageService:
    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
        )
        self.bucket = S3_BUCKET

    def generate_object_key(self, record_id: str, filename: str) -> str:
        ext = filename.split(".")[-1] if "." in filename else ""
        return f"{record_id}/{uuid.uuid4()}.{ext}"

    def upload(self, *, object_key: str, file, content_type: str | None = None,):
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        self.client.upload_fileobj(
            Fileobj=file,
            Bucket=self.bucket,
            Key=object_key,
            ExtraArgs=extra_args,
        )

    def delete(self, *, object_key: str) -> None:
        self.client.delete_object(
            Bucket=self.bucket,
            Key=object_key,
        )

    def generate_download_url(self, *, object_key: str, original_filename: str, expires: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": self.bucket,
                "Key": object_key,
                "ResponseContentDisposition": f'attachment; filename="{original_filename}"',
            },
            ExpiresIn=expires,
        )
        