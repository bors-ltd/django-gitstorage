from django.conf import settings

import appconf


class AppConf(appconf.AppConf):
    GITSTORAGE_REPOSITORY = 'repo'
    GITSTORAGE_BLOB_MODEL = 'gitstorage.Blob'
    # As we are aiming at serving these files directly by the webserver (X-Accel-Redirect),
    # it would hardly support any other storage method
    GITSTORAGE_DATA_STORAGE = 'django.core.files.storage.FileSystemStorage'
    GITSTORAGE_DATA_ROOT = 'gitstorage'
    # For X-Accel-Redirect, as data must not be directly exposed
    GITSTORAGE_DATA_URL = '/data/'
