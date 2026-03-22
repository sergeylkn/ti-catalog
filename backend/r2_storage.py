"""
R2 Storage integration for Cloudflare
Downloads and manages PDFs from R2 bucket
"""
import os
import boto3
from typing import List
from pathlib import Path

class R2StorageClient:
    """
    Cloudflare R2 Storage client
    Uses S3-compatible API
    """

    def __init__(self):
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.access_key = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        self.secret_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        self.bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET", "product-pdfs")
        self.endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"

        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='auto'
        )

    def list_files(self, prefix: str = "") -> List[str]:
        """List all PDF files in bucket"""
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            files = []
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents'] if obj['Key'].endswith('.pdf')]
            return files
        except Exception as e:
            print(f"Error listing files: {e}")
            return []

    def download_file(self, file_key: str, local_path: str) -> bool:
        """Download PDF from R2 to local storage"""
        try:
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            self.client.download_file(self.bucket_name, file_key, local_path)
            print(f"✅ Downloaded: {file_key} → {local_path}")
            return True
        except Exception as e:
            print(f"❌ Error downloading {file_key}: {e}")
            return False

    def upload_file(self, local_path: str, file_key: str) -> bool:
        """Upload file to R2"""
        try:
            self.client.upload_file(local_path, self.bucket_name, file_key)
            print(f"✅ Uploaded: {local_path} → {file_key}")
            return True
        except Exception as e:
            print(f"❌ Error uploading {local_path}: {e}")
            return False

    def get_public_url(self, file_key: str) -> str:
        """Get public URL for file"""
        base_url = os.getenv("CLOUDFLARE_R2_PUBLIC_URL", 
                             f"https://pub-ada201ec5fb84401a3b36b7b21e6ed0f.r2.dev")
        return f"{base_url}/{file_key}"


def get_r2_client() -> R2StorageClient:
    """Factory function for R2 client"""
    try:
        return R2StorageClient()
    except Exception as e:
        print(f"⚠️  R2 client initialization failed: {e}")
        return None


if __name__ == "__main__":
    # Test R2 client
    r2 = R2StorageClient()

    # List PDFs from manifest
    files = r2.list_files()
    print(f"Found {len(files)} PDFs in R2:")
    for f in files[:5]:
        print(f"  - {f}")

    # Example: Download first PDF
    if files:
        local_path = f"/tmp/{files[0]}"
        r2.download_file(files[0], local_path)
        print(f"Public URL: {r2.get_public_url(files[0])}")
