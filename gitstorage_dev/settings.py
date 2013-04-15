# Django settings for gitstorage_dev project.
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': "django.db.backends.sqlite3",
        'NAME': ":memory:",
        'USER': "",
        'PASSWORD': "",
        'HOST': "",
        'PORT': "",
    }
}

TIME_ZONE = 'Europe/Paris'

LANGUAGE_CODE = 'fr-fr'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'

SECRET_KEY = 'secret'

ROOT_URLCONF = 'gitstorage_dev.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'south',
    'gitstorage',
)

LOGGING = {
    'version': 1,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
}

TEST_RUNNER = "discover_runner.DiscoverRunner"
TEST_DISCOVER_TOP_LEVEL = PROJECT_ROOT
TEST_DISCOVER_ROOT = PROJECT_ROOT
TEST_DISCOVER_PATTERN = "test_*"
