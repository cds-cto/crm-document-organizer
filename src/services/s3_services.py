import boto3
from typing import Optional

class S3Service:
    def __init__(
        self,
        *,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region: str,
        bucket_name: str,
        folder_name: str,
    ):
        self.bucket_name = bucket_name
        self.folder_name = folder_name
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region,
        )

    def get_file_bytes(self, file_name: str) -> Optional[bytes]:
        s3_key = f"{self.folder_name}/{file_name}"
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response["Body"].read()
        except Exception as e:
            print(f"❌ Failed to get file from S3: {file_name} — {e}")
            return None
