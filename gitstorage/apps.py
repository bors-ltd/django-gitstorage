from django.apps import AppConfig
from django.conf import settings


def set_default(name, default_value):
    if getattr(settings, name, None) is None:
        setattr(settings, name, default_value)


class GitStorageConfig(AppConfig):
    name = 'gitstorage'
    verbose_name = "GitStorage"

    # Here are all the settings, although AppConfig is not really designed for this
    set_default('GITSTORAGE_REPOSITORY', 'repo')
    set_default('GITSTORAGE_BLOB_MODEL', 'gitstorage.Blob')
    # As we are aiming at serving these files directly by the webserver (X-Accel-Redirect),
    # it would hardly support any other storage method
    set_default('GITSTORAGE_DATA_STORAGE', 'django.core.files.storage.FileSystemStorage')
    set_default('GITSTORAGE_DATA_ROOT', 'gitstorage')
