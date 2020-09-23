from django.conf import settings  # noqa keep this import

import appconf


class AppConf(appconf.AppConf):
    # Path the the repository to browse
    GITSTORAGE_REPOSITORY = "repo"

    class Meta:
        # Effing appconf...
        prefix = ""
