"""
Use at your own risk!

* I don't know if this will work with any storage backend other than FileSystemStorage, but it might.
* I don't expect this to work when using multiple sites with cache prefixes. In this case it's probably best to have a
  separate cache for imagekit and flush the whole thing.
* It only works with the source_name_dot_hash namer.

For these reasons this remains an undocumented and untested feature.
"""

import re
from pathlib import Path

from django.conf import settings
from django.core.cache import caches
from django.core.files.storage import get_storage_class
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = (
        "Deletes generated files for sources that no longer exist.  Ie you clean up your media files and this will"
        "clean up the imagekit files.  Suggest running once per day."
    )
    storage = None
    static_storage = None
    root_path = None
    cache = None

    def file_exists(self, path, file):
        """
        Check the storage and static storage for the file.
        The file can have a different extension.
        """
        file_stem = Path(file).stem
        for storage in [self.storage, self.static_storage]:
            try:
                directories, files = storage.listdir(path)
            except FileNotFoundError:
                continue

            for f in files:
                if Path(f).stem == file_stem:
                    return True

        return False

    def process_file(self, file, path):
        """
        Delete images that no longer have a source.
        """
        source_path = path.relative_to(self.root_path)
        source_file = re.sub(r"\.[a-z0-9]+\.", ".", file)  # noqa

        if not self.file_exists(source_path, source_file):
            filepath = path / file

            cache_key = f"{settings.IMAGEKIT_CACHE_PREFIX}{filepath.relative_to(self.root_path.parent)}-state"
            self.cache.delete(cache_key)

            self.storage.delete(filepath)
            self.stdout.write(f"Deleted: {filepath}")

    def process_directory(self, path):
        """
        Recursively walk through directories.
        """
        directories, files = self.storage.listdir(path)

        for file in files:
            self.process_file(file, path)

        for directory in directories:
            next_path = path / directory

            self.process_directory(next_path)

            # Delete empty dirs
            if not any(self.storage.listdir(next_path)):
                self.storage.delete(next_path)

    def handle(self, *args, **options):
        """
        Using the appropriate storage walk through the directories in settings.IMAGEKIT_CACHEFILE_DIR
        For each image file find its source name by removing the hash and settings.IMAGEKIT_CACHEFILE_DIR
        Check if the source exists in media or static if it does continue
        If the source doesn't exist delete the imagekit file, work out the cache key and delete from cache
        """
        compatible_namer = "imagekit.cachefiles.namers.source_name_dot_hash"
        if not settings.IMAGEKIT_SPEC_CACHEFILE_NAMER == compatible_namer:
            self.stdout.write(
                "imagekit_cleanup will only work if you use the %s namer."
                % compatible_namer
            )
            return

        self.storage = get_storage_class(settings.IMAGEKIT_DEFAULT_FILE_STORAGE)()
        self.static_storage = get_storage_class(settings.STATICFILES_STORAGE)()
        self.cache = caches[settings.IMAGEKIT_CACHE_BACKEND]

        try:
            path = Path(self.storage.location)
        except AttributeError:
            path = Path("/")

        self.root_path = path / settings.IMAGEKIT_CACHEFILE_DIR

        self.process_directory(self.root_path)
