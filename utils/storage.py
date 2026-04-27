"""
Supabase Storage backend for Django.
Integrates Supabase Storage with Django's File Storage API.
"""
import logging
from django.conf import settings
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from supabase import create_client

logger = logging.getLogger(__name__)


class SupabaseStorage(Storage):
    """
    Custom storage backend for Supabase Storage.

    Uses SUPABASE_URL, SUPABASE_KEY, and SUPABASE_BUCKET from Django settings.
    Files are stored in the 'products/images/' folder within the bucket.
    """

    def __init__(self, bucket_name=None, folder_prefix="products/images/"):
        """
        Initialize Supabase client.

        Args:
            bucket_name: Supabase storage bucket name (defaults to SUPABASE_BUCKET setting)
            folder_prefix: Folder prefix for uploaded files (default: products/images/)
        """
        self.bucket_name = bucket_name or getattr(settings, "SUPABASE_BUCKET", None)
        self.folder_prefix = folder_prefix

        supabase_url = getattr(settings, "SUPABASE_URL", None)
        supabase_key = getattr(settings, "SUPABASE_KEY", None)

        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be configured in Django settings."
            )

        self.client = create_client(supabase_url, supabase_key)

    def _get_full_path(self, name):
        """Get the full path in Supabase storage including folder prefix."""
        if name.startswith(self.folder_prefix):
            return name
        return f"{self.folder_prefix}{name}"

    def _save(self, name, content):
        """
        Save the file to Supabase Storage.

        Args:
            name: Filename (relative to folder_prefix)
            content: File-like object or ContentFile

        Returns:
            The full path of the saved file
        """
        full_path = self._get_full_path(name)

        # Read content if it's a file-like object
        if hasattr(content, "read"):
            file_content = content.read()
        else:
            file_content = content

        try:
            # Upload to Supabase Storage
            response = self.client.storage.from_(self.bucket_name).upload(
                full_path,
                file_content,
                {"content-type": getattr(content, "content_type", "image/jpeg")}
            )

            logger.info(f"Successfully uploaded file to Supabase: {full_path}")
            return full_path

        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {e}")
            raise

    def _open(self, name, mode="rb"):
        """
        Open a file from Supabase Storage.

        Args:
            name: Filename (relative to folder_prefix)
            mode: File mode (only 'rb' supported for remote storage)

        Returns:
            ContentFile with the file content
        """
        full_path = self._get_full_path(name)

        try:
            response = self.client.storage.from_(self.bucket_name).download(full_path)
            return ContentFile(response)

        except Exception as e:
            logger.error(f"Error downloading file from Supabase: {e}")
            raise

    def exists(self, name):
        """
        Check if a file exists in Supabase Storage.

        Args:
            name: Filename (relative to folder_prefix)

        Returns:
            True if file exists, False otherwise
        """
        full_path = self._get_full_path(name)

        try:
            response = self.client.storage.from_(self.bucket_name).list(full_path.rsplit("/", 1)[0])
            file_name = full_path.rsplit("/", 1)[1]
            return any(file["name"] == file_name for file in response)

        except Exception as e:
            logger.error(f"Error checking file existence in Supabase: {e}")
            return False

    def url(self, name):
        """
        Get the public URL for a file in Supabase Storage.

        Args:
            name: Filename (relative to folder_prefix)

        Returns:
            Public URL string
        """
        full_path = self._get_full_path(name)

        try:
            response = self.client.storage.from_(self.bucket_name).get_public_url(full_path)
            return response

        except Exception as e:
            logger.error(f"Error getting public URL from Supabase: {e}")
            raise

    def delete(self, name):
        """
        Delete a file from Supabase Storage.

        Args:
            name: Filename (relative to folder_prefix)
        """
        full_path = self._get_full_path(name)

        try:
            self.client.storage.from_(self.bucket_name).remove([full_path])
            logger.info(f"Successfully deleted file from Supabase: {full_path}")

        except Exception as e:
            logger.error(f"Error deleting file from Supabase: {e}")
            raise

    def get_valid_name(self, name):
        """Return a valid filename (strip special characters)."""
        import re
        name = re.sub(r"[^\w\-.]", "_", name)
        return name

    def get_available_name(self, name, max_length=None):
        """Return a filename that is available in the storage."""
        if not self.exists(name):
            return name

        # If file exists, add a unique suffix
        import uuid
        name_parts = name.rsplit(".", 1)
        if len(name_parts) == 2:
            unique_name = f"{name_parts[0]}_{uuid.uuid4().hex[:8]}.{name_parts[1]}"
        else:
            unique_name = f"{name}_{uuid.uuid4().hex[:8]}"

        return unique_name
