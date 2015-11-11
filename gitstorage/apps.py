from django.apps import AppConfig


class GitStorageConfig(AppConfig):
    name = 'gitstorage'
    verbose_name = "GitStorage"

    # Are these settings or config?
    REFERENCE_NAME = 'refs/heads/master'
    AUTHOR = COMMITTER = ("Git Storage", "git@storage")
    INITIAL_COMMIT_MESSAGE = "Initial commit by Git Storage"
    SAVE_MESSAGE = "Saved by Git Storage"
    DELETE_MESSAGE = "Deleted by Git Storage"
