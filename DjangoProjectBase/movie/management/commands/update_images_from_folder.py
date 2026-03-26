import os
import re
import unicodedata

from django.conf import settings
from django.core.management.base import BaseCommand
from movie.models import Movie


class Command(BaseCommand):
    help = "Update movie images from files in media/movie/images/"

    def normalize_name(self, text):
        """
        Normalize text so titles and file names can be compared more easily.
        Example:
        'Baby's Dinner' -> 'babysdinner'
        """
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")
        text = text.lower()
        text = re.sub(r"^m_", "", text)          # removes m_ prefix from file names
        text = re.sub(r"\.[^.]+$", "", text)     # removes extension
        text = re.sub(r"[^a-z0-9]+", "", text)   # keeps only letters/numbers
        return text

    def handle(self, *args, **kwargs):
        images_dir = os.path.join(settings.MEDIA_ROOT, "movie", "images")

        if not os.path.exists(images_dir):
            self.stderr.write(
                self.style.ERROR(f"Folder not found: {images_dir}")
            )
            return

        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".jfif", ".JPG", ".JPEG", ".PNG", ".WEBP"}
        image_files = [
            f for f in os.listdir(images_dir)
            if os.path.isfile(os.path.join(images_dir, f))
            and os.path.splitext(f)[1] in valid_extensions
        ]

        if not image_files:
            self.stderr.write(
                self.style.WARNING("No image files found in media/movie/images/")
            )
            return

        # Build an index: normalized filename -> real filename
        image_map = {}
        for filename in image_files:
            normalized = self.normalize_name(filename)
            image_map[normalized] = filename

        movies = Movie.objects.all()
        updated_count = 0
        not_found_count = 0

        self.stdout.write(f"Found {movies.count()} movies")
        self.stdout.write(f"Found {len(image_files)} image files")

        for movie in movies:
            normalized_title = self.normalize_name(movie.title)

            if normalized_title in image_map:
                filename = image_map[normalized_title]
                relative_path = f"movie/images/{filename}"

                movie.image = relative_path
                movie.save(update_fields=["image"])
                updated_count += 1

                self.stdout.write(
                    self.style.SUCCESS(f"Updated: {movie.title} -> {relative_path}")
                )
            else:
                not_found_count += 1
                self.stderr.write(
                    self.style.WARNING(f"No image found for: {movie.title}")
                )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"Finished. Updated {updated_count} movies."))
        self.stdout.write(self.style.WARNING(f"Not found: {not_found_count} movies."))