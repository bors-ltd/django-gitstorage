from django.conf import settings  # noqa keep this import

import appconf


class AppConf(appconf.AppConf):
    GITSTORAGE_REPOSITORY = "repo"
    GITSTORAGE_BLOB_MODEL = "gitstorage.Blob"
    # As we are aiming at serving these files directly by the webserver (X-Accel-Redirect),
    # it would hardly support any other storage method
    GITSTORAGE_DATA_STORAGE = "django.core.files.storage.FileSystemStorage"
    # For X-Accel-Redirect, as data must not be directly exposed
    GITSTORAGE_DATA_URL = "/data/"
    # Don't forget the django-sendfile2 mandatory setting to actual files being served
    # It must be absolute to compare to the absolute path of the file served
    # SENDFILE_ROOT = ...

    class Meta:
        # Effing appconf...
        prefix = ""
