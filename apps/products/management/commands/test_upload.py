"""
Management command to test Supabase Storage image upload.

Usage:
    python manage.py test_upload <path_to_image>

Example:
    python manage.py test_upload test_image.jpg
"""
import os
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.files.base import ContentFile

from utils.storage import SupabaseStorage


class Command(BaseCommand):
    help = "Test uploading an image to Supabase Storage"

    def add_arguments(self, parser):
        parser.add_argument(
            "image_path",
            type=str,
            help="Path to the image file to upload"
        )

    def handle(self, *args, **options):
        image_path = options["image_path"]

        # Check if file exists
        if not os.path.exists(image_path):
            raise CommandError(f"Image file not found: {image_path}")

        # Validate Supabase settings
        if not settings.SUPABASE_URL:
            raise CommandError("SUPABASE_URL not configured in settings")
        if not settings.SUPABASE_KEY:
            raise CommandError("SUPABASE_KEY not configured in settings")
        if not settings.SUPABASE_BUCKET:
            raise CommandError("SUPABASE_BUCKET not configured in settings")

        self.stdout.write(self.style.SUCCESS(
            f"Supabase configured:\n"
            f"  URL: {settings.SUPABASE_URL}\n"
            f"  Bucket: {settings.SUPABASE_BUCKET}"
        ))

        # Read the image file
        with open(image_path, "rb") as f:
            image_content = f.read()

        self.stdout.write(f"Reading image: {image_path} ({len(image_content)} bytes)")

        # Initialize storage
        storage = SupabaseStorage()
        self.stdout.write("Initialized SupabaseStorage")

        # Generate filename
        import uuid
        filename = os.path.basename(image_path)
        unique_name = f"{uuid.uuid4().hex}_{filename}"

        # Upload to Supabase
        self.stdout.write("Uploading to Supabase...")
        content_file = ContentFile(image_content)
        content_file.content_type = self._guess_content_type(filename)

        saved_path = storage.save(unique_name, content_file)
        self.stdout.write(self.style.SUCCESS(f"Saved as: {saved_path}"))

        # Get public URL
        public_url = storage.url(unique_name)
        self.stdout.write(self.style.SUCCESS(
            f"\nUpload successful!\n"
            f"Public URL: {public_url}\n"
            f"\nYou can verify the image appears in your Supabase Storage dashboard."
        ))

    def _guess_content_type(self, filename):
        """Guess content type from file extension."""
        ext = filename.split(".")[-1].lower()
        content_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
        }
        return content_types.get(ext, "image/jpeg")
