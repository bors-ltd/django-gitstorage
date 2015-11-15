# Copyright Bors LTD
# This file is part of django-gitstorage.
#
#    Django-gitstorage is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Django-gitstorage is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with django-gitstorage.  If not, see <http://www.gnu.org/licenses/>.

from io import BytesIO
import os
from urllib.parse import urljoin

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files import storage, File
from django.conf import settings
from django.utils.encoding import filepath_to_uri
from django.utils._os import safe_join, abspathu

import pygit2

from . import wrappers


app_config = apps.get_app_config('gitstorage')


class GitStorage(storage.Storage):

    def __init__(self, location=None, base_url=None):
        """
            Initialize a Git repository or open an existing one.

            @param location: path where to create and open the repository
        """
        if not location:
            location = getattr(settings, 'GIT_STORAGE_ROOT', "")
            if not location:
                raise ImproperlyConfigured("GIT_STORAGE_ROOT is required")
        self.base_location = location
        self.location = abspathu(self.base_location)
        if base_url is None:
            try:
                base_url = settings.GIT_STORAGE_URL
            except AttributeError:
                base_url = None
        self.base_url = base_url

        # Create the repository as necessary
        if not os.path.exists(location):
            self._create()

        # Open the repository with our class
        self.repository = wrappers.Repository(self.location)
        assert self.repository.is_bare

        # Author of the following commits
        self.author_signature = self.repository.default_signature

    #
    # Private Git-specific methods
    #

    def _git_path(self, name):
        """Clean path name and make it relative to the repository root.

         Taken from FileSystemStorage.path.

            @param name: file path, relative to the repository root
            @return: cleaned path
        """
        path = safe_join(self.location, name)
        path = os.path.normpath(path)
        # Strip off the repo absolute path
        path = path[len(self.location) + 1:]
        return path

    def _create(self):
        repository = pygit2.init_repository(self.location, bare=True)

        # Initial config (yes hardcoded... but you can change it afterwards)
        repository.config['user.name'] = "Git Storage"
        repository.config['user.email'] = "git@storage"

        # Initial commit
        tree_id = repository.TreeBuilder().write()
        repository.create_commit(
            app_config.REFERENCE_NAME,
            repository.default_signature,  # Author signature from repository/config [user]
            repository.default_signature,  # Committer signature from repository/config [user]
            app_config.INITIAL_COMMIT_MESSAGE,
            tree_id,
            [],
        )

    def _commit(self, message, tree):
        """Commit the given tree using this commit message.

            @param message: text message
            @param tree: tree id
            @return: commit id
        """
        self.repository.create_commit(
            self.repository.head.name,
            self.author_signature,
            self.repository.default_signature,  # Committer signature from repository/config [user]
            message,
            tree,
            [self.repository.head.target],
        )

    #
    # Public Git-specific methods
    #

    def set_author(self, user):
        """
        Set the current author for the following commits (through save() and delete().

        :param user: User model (or compatible) instance

        This state is stored not to modify save() and delete() signatures. This also means you must remember to
        set another author as required.

        Designed with a repository reopened at each web request in mind.
        """
        self.author_signature = pygit2.Signature(user.get_full_name(), user.email, encoding='utf8')

    # Implementations of high-level open() and save()

    def _open(self, name, mode='rb'):
        """Open the given file name, always in 'rb' mode.

            @param: name: file path, relative to the repository root
            @return: File object
        """
        if mode != 'rb':
            raise ImproperlyConfigured("Can't rewrite Git files, just save on the same path")
        path = self._git_path(name)
        blob = self.repository.open(path)
        # TODO Yes, we're loading a potentially big file in memory
        # pygit2 may offer later a lazy map to the blob data as a file-like
        return File(BytesIO(blob.data), name=name)

    def _save(self, name, content):
        """Save the File content under the given path name.

            @param name: file path, relative to the repository root
            @param content: File content (temporary or in-memory file object)
            @return: the name under which the content was saved
        """
        path = self._git_path(name)
        if hasattr(content, 'temporary_file_path'):
            blob_id = self.repository.create_blob_fromdisk(content.temporary_file_path())
            content.close()
        else:
            # TODO Yes, we're loading a potentially big file in memory
            # Use create_blob_fromfilelike or something when available
            blob_id = self.repository.create_blob(content.read())
        # The index is a flatten representation of the repository tree
        index = self.repository.index
        index.add(pygit2.IndexEntry(path, blob_id, pygit2.GIT_FILEMODE_BLOB))
        tree_id = index.write_tree()
        self._commit(app_config.SAVE_MESSAGE, tree_id)
        return name

    #
    # Overriding when it doesn't make sense for a git repo
    #

    def get_available_name(self, name, max_length=None):
        """Always allow to overwrite an existing name. We're not implementing a storage for media upload.

            @param: name: file path, relative to the repository root
        """
        return self._git_path(name)

    def path(self, name):
        raise NotImplementedError("Git blobs cannot be open through a path.")

    #
    # Now implementing abstract Storage methods (except path() on purpose)
    #

    def delete(self, name):
        """Delete the blob at the given path name by committing a tree without it.

            @param: name: file path, relative to the repository root
        """
        path = self._git_path(name)
        # The index is a flatten representation of the repository tree
        index = self.repository.index
        index.remove(path)
        tree_id = index.write_tree()
        self._commit(app_config.DELETE_MESSAGE, tree_id)

    def exists(self, name):
        """Search the given name in the repository.

            @param: name: file path, relative to the repository root
        """
        path = self._git_path(name)
        return path in self.repository.tree

    def listdir(self, path):
        """List the contents of the given path.

            @param: path: tree path, relative to the repository root
            @return: ([], []) trees and blobs

        Contrary to a filesystem listdir, we expose tree entries, and keep the notion of blobs and trees.
        """
        path = self._git_path(path)
        tree = self.repository.open(path)
        trees, blobs = [], []
        for entry in tree:
            if entry.type == "blob":
                blobs.append(entry)
            elif entry.type == "tree":
                trees.append(entry)
        return trees, blobs

    def size(self, name):
        """Return the size of the blob at the given path name.

            @param: name: file path, relative to the repository root
        """
        path = self._git_path(name)
        blob = self.repository.open(path)
        return blob.size

    def url(self, name):
        path = self._git_path(name)
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")
        return urljoin(self.base_url, filepath_to_uri(path))

    # accessed_time doesn't make sense for a git repo
    # created_time would be the time of the first commit adding this blob, but costly
    # It would remain modified_time, but for what it's worth...
