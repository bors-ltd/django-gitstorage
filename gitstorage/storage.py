from django.conf import settings
from django.utils.functional import LazyObject
from django.utils.module_loading import import_string


def get_storage_class(import_path=None):
    return import_string(import_path or settings.GITSTORAGE_DATA_STORAGE)


class DefaultStorage(LazyObject):
    def _setup(self):
        self._wrapped = get_storage_class()(
            location=settings.SENDFILE_ROOT,
            base_url=settings.GITSTORAGE_DATA_URL,  # Served by webserver for X-Accel-Redirect
        )


default_storage = DefaultStorage()
