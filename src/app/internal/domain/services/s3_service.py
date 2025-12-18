import os
import boto3
from datetime import timedelta
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
        ext = filename.split(".")[-1]
        return f"records/{record_id}/{uuid.uuid4()}.{ext}"

    def upload(self, *, object_key: str, file_bytes: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=object_key,
            Body=file_bytes,
            ContentType=content_type,
        )

    def delete(self, *, object_key: str) -> None:
        self.client.delete_object(
            Bucket=self.bucket,
            Key=object_key,
        )
