from django.conf import settings  # keep this import

import appconf


class AppConf(appconf.AppConf):
    GITSTORAGE_REPOSITORY = "repo"
    GITSTORAGE_BLOB_MODEL = "gitstorage.Blob"
    # As we are aiming at serving these files directly by the webserver (X-Accel-Redirect),
    # it would hardly support any other storage method
    GITSTORAGE_DATA_STORAGE = "django.core.files.storage.FileSystemStorage"
    # Be warned this is a relative path by default,
    # when you run sync_blobs outside the project directory
    GITSTORAGE_DATA_ROOT = "data"
    # For X-Accel-Redirect, as data must not be directly exposed
    GITSTORAGE_DATA_URL = "/data/"
