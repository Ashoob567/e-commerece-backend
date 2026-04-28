"""
Mock Supabase Storage for testing.
Avoids real HTTP calls during tests.
"""
from django.core.files.base import ContentFile
from django.core.files.storage import Storage


class MockSupabaseStorage(Storage):
    """Mock storage backend for testing Supabase integration."""

    def __init__(self, bucket_name=None, folder_prefix="products/images/"):
        self.bucket_name = bucket_name or "test-bucket"
        self.folder_prefix = folder_prefix
        self._files = {}  # In-memory file storage

    def _get_full_path(self, name):
        if name.startswith(self.folder_prefix):
            return name
        return f"{self.folder_prefix}{name}"

    def _save(self, name, content):
        full_path = self._get_full_path(name)
        if hasattr(content, "read"):
            self._files[full_path] = content.read()
        else:
            self._files[full_path] = content
        return full_path

    def _open(self, name, mode="rb"):
        full_path = self._get_full_path(name)
        if full_path in self._files:
            return ContentFile(self._files[full_path])
        raise FileNotFoundError(f"File {full_path} not found")

    def exists(self, name):
        full_path = self._get_full_path(name)
        return full_path in self._files

    def url(self, name):
        full_path = self._get_full_path(name)
        if not self.exists(name):
            raise FileNotFoundError(f"File {full_path} not found")
        return f"https://test.supabase.co/storage/v1/object/public/{self.bucket_name}/{full_path}"

    def delete(self, name):
        full_path = self._get_full_path(name)
        if full_path in self._files:
            del self._files[full_path]

    def get_valid_name(self, name):
        import re
        return re.sub(r"[^\w\-.]", "_", name)

    def get_available_name(self, name, max_length=None):
        if not self.exists(name):
            return name
        import uuid
        name_parts = name.rsplit(".", 1)
        if len(name_parts) == 2:
            return f"{name_parts[0]}_{uuid.uuid4().hex[:8]}.{name_parts[1]}"
        return f"{name}_{uuid.uuid4().hex[:8]}"
