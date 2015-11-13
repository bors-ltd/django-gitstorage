from django.apps import AppConfig


class GitStorageConfig(AppConfig):
    name = 'gitstorage'
    verbose_name = "GitStorage"

    # Are these settings or config? They could even be read from the repository's config
    REFERENCE_NAME = 'refs/heads/master'
    INITIAL_COMMIT_MESSAGE = "Initial commit by Git Storage"
    SAVE_MESSAGE = "Saved by Git Storage"
    DELETE_MESSAGE = "Deleted by Git Storage"
