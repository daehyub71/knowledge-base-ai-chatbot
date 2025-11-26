"""Google Cloud Storage client for file management."""

import logging
from pathlib import Path
from typing import BinaryIO

from google.cloud import storage
from google.cloud.exceptions import NotFound

from app.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)


class StorageClient:
    """Client for Google Cloud Storage operations."""

    def __init__(
        self,
        bucket_name: str | None = None,
        credentials_path: str | None = None,
    ):
        """Initialize the storage client.

        Args:
            bucket_name: GCS bucket name (uses settings if not provided)
            credentials_path: Path to service account JSON file
        """
        self.bucket_name = bucket_name or settings.GCS_BUCKET_NAME

        # Initialize GCS client
        if credentials_path:
            self.client = storage.Client.from_service_account_json(credentials_path)
        else:
            # Uses GOOGLE_APPLICATION_CREDENTIALS env var or default credentials
            self.client = storage.Client()

        self._bucket = None

        logger.info(f"StorageClient initialized for bucket: {self.bucket_name}")

    @property
    def bucket(self) -> storage.Bucket:
        """Get the GCS bucket object.

        Returns:
            GCS Bucket object
        """
        if self._bucket is None:
            self._bucket = self.client.bucket(self.bucket_name)
        return self._bucket

    def upload_file(
        self,
        local_path: str | Path,
        gcs_path: str,
        content_type: str | None = None,
    ) -> str:
        """Upload a local file to GCS.

        Args:
            local_path: Path to local file
            gcs_path: Destination path in GCS (blob name)
            content_type: MIME type of the file

        Returns:
            GCS URI (gs://bucket/path)
        """
        local_path = Path(local_path)

        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        blob = self.bucket.blob(gcs_path)

        if content_type:
            blob.content_type = content_type

        blob.upload_from_filename(str(local_path))

        gcs_uri = f"gs://{self.bucket_name}/{gcs_path}"
        logger.info(f"Uploaded {local_path} to {gcs_uri}")

        return gcs_uri

    def upload_from_string(
        self,
        data: str | bytes,
        gcs_path: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload data directly to GCS.

        Args:
            data: String or bytes data to upload
            gcs_path: Destination path in GCS
            content_type: MIME type of the data

        Returns:
            GCS URI
        """
        blob = self.bucket.blob(gcs_path)
        blob.content_type = content_type

        if isinstance(data, str):
            blob.upload_from_string(data, content_type=content_type)
        else:
            blob.upload_from_string(data, content_type=content_type)

        gcs_uri = f"gs://{self.bucket_name}/{gcs_path}"
        logger.info(f"Uploaded data to {gcs_uri}")

        return gcs_uri

    def upload_from_file(
        self,
        file_obj: BinaryIO,
        gcs_path: str,
        content_type: str | None = None,
    ) -> str:
        """Upload from a file-like object to GCS.

        Args:
            file_obj: File-like object to upload
            gcs_path: Destination path in GCS
            content_type: MIME type of the file

        Returns:
            GCS URI
        """
        blob = self.bucket.blob(gcs_path)

        if content_type:
            blob.content_type = content_type

        blob.upload_from_file(file_obj)

        gcs_uri = f"gs://{self.bucket_name}/{gcs_path}"
        logger.info(f"Uploaded file object to {gcs_uri}")

        return gcs_uri

    def download_file(
        self,
        gcs_path: str,
        local_path: str | Path,
    ) -> Path:
        """Download a file from GCS to local path.

        Args:
            gcs_path: Source path in GCS
            local_path: Destination local path

        Returns:
            Path to downloaded file
        """
        local_path = Path(local_path)
        local_path.parent.mkdir(parents=True, exist_ok=True)

        blob = self.bucket.blob(gcs_path)

        if not blob.exists():
            raise FileNotFoundError(f"GCS file not found: gs://{self.bucket_name}/{gcs_path}")

        blob.download_to_filename(str(local_path))

        logger.info(f"Downloaded gs://{self.bucket_name}/{gcs_path} to {local_path}")
        return local_path

    def download_as_bytes(self, gcs_path: str) -> bytes:
        """Download a file from GCS as bytes.

        Args:
            gcs_path: Source path in GCS

        Returns:
            File contents as bytes
        """
        blob = self.bucket.blob(gcs_path)

        if not blob.exists():
            raise FileNotFoundError(f"GCS file not found: gs://{self.bucket_name}/{gcs_path}")

        data = blob.download_as_bytes()

        logger.info(f"Downloaded gs://{self.bucket_name}/{gcs_path} ({len(data)} bytes)")
        return data

    def download_as_string(self, gcs_path: str) -> str:
        """Download a file from GCS as string.

        Args:
            gcs_path: Source path in GCS

        Returns:
            File contents as string
        """
        data = self.download_as_bytes(gcs_path)
        return data.decode("utf-8")

    def file_exists(self, gcs_path: str) -> bool:
        """Check if a file exists in GCS.

        Args:
            gcs_path: Path in GCS to check

        Returns:
            True if file exists, False otherwise
        """
        blob = self.bucket.blob(gcs_path)
        exists = blob.exists()

        logger.debug(f"File exists check: gs://{self.bucket_name}/{gcs_path} = {exists}")
        return exists

    def delete_file(self, gcs_path: str) -> bool:
        """Delete a file from GCS.

        Args:
            gcs_path: Path in GCS to delete

        Returns:
            True if deleted, False if not found
        """
        blob = self.bucket.blob(gcs_path)

        try:
            blob.delete()
            logger.info(f"Deleted gs://{self.bucket_name}/{gcs_path}")
            return True
        except NotFound:
            logger.warning(f"File not found for deletion: gs://{self.bucket_name}/{gcs_path}")
            return False

    def list_files(
        self,
        prefix: str | None = None,
        delimiter: str | None = None,
    ) -> list[str]:
        """List files in the bucket.

        Args:
            prefix: Filter by path prefix
            delimiter: Delimiter for directory-like listing

        Returns:
            List of blob names
        """
        blobs = self.client.list_blobs(
            self.bucket_name,
            prefix=prefix,
            delimiter=delimiter,
        )

        files = [blob.name for blob in blobs]

        logger.debug(f"Listed {len(files)} files with prefix='{prefix}'")
        return files

    def get_file_metadata(self, gcs_path: str) -> dict:
        """Get metadata for a file in GCS.

        Args:
            gcs_path: Path in GCS

        Returns:
            Dictionary with file metadata
        """
        blob = self.bucket.blob(gcs_path)

        if not blob.exists():
            raise FileNotFoundError(f"GCS file not found: gs://{self.bucket_name}/{gcs_path}")

        blob.reload()

        return {
            "name": blob.name,
            "size": blob.size,
            "content_type": blob.content_type,
            "created": blob.time_created,
            "updated": blob.updated,
            "md5_hash": blob.md5_hash,
            "crc32c": blob.crc32c,
        }

    def copy_file(
        self,
        source_path: str,
        destination_path: str,
        destination_bucket: str | None = None,
    ) -> str:
        """Copy a file within or between buckets.

        Args:
            source_path: Source path in GCS
            destination_path: Destination path in GCS
            destination_bucket: Destination bucket (uses same bucket if not specified)

        Returns:
            GCS URI of the copied file
        """
        source_blob = self.bucket.blob(source_path)

        if not source_blob.exists():
            raise FileNotFoundError(
                f"Source file not found: gs://{self.bucket_name}/{source_path}"
            )

        if destination_bucket:
            dest_bucket = self.client.bucket(destination_bucket)
        else:
            dest_bucket = self.bucket
            destination_bucket = self.bucket_name

        self.bucket.copy_blob(source_blob, dest_bucket, destination_path)

        gcs_uri = f"gs://{destination_bucket}/{destination_path}"
        logger.info(f"Copied to {gcs_uri}")

        return gcs_uri

    def generate_signed_url(
        self,
        gcs_path: str,
        expiration_minutes: int = 60,
    ) -> str:
        """Generate a signed URL for temporary access.

        Args:
            gcs_path: Path in GCS
            expiration_minutes: URL expiration time in minutes

        Returns:
            Signed URL string
        """
        from datetime import timedelta

        blob = self.bucket.blob(gcs_path)

        if not blob.exists():
            raise FileNotFoundError(f"GCS file not found: gs://{self.bucket_name}/{gcs_path}")

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET",
        )

        logger.info(f"Generated signed URL for {gcs_path} (expires in {expiration_minutes} min)")
        return url
