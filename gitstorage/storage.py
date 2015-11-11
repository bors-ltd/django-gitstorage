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
            try:
                location = settings.GIT_STORAGE_ROOT
            except AttributeError:
                raise ImproperlyConfigured("GIT_STORAGE_ROOT is required")
        self.base_location = location
        self.location = abspathu(self.base_location)
        if base_url is None:
            try:
                base_url = settings.GIT_STORAGE_URL
            except AttributeError:
                base_url = None
        self.base_url = base_url

        # Create the repository
        if not os.path.exists(location):
            self._create()

        # Open the repository with our class
        self.repository = wrappers.Repository(self.location)
        assert self.repository.is_bare

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

        # Initial commit
        author = pygit2.Signature(app_config.AUTHOR[0], app_config.AUTHOR[1])
        committer = pygit2.Signature(app_config.COMMITTER[0], app_config.COMMITTER[1])
        tree = repository.TreeBuilder().write()
        repository.create_commit(
            app_config.REFERENCE_NAME,
            author,
            committer,
            app_config.INITIAL_COMMIT_MESSAGE,
            tree,
            [],
        )

    def _open(self, name, mode='rb'):
        """Open the given file name, always in 'rb' mode.

            @param: name: file path, relative to the repository root
            @return: File object
        """
        if mode != 'rb':
            raise ImproperlyConfigured("Can't rewrite Git files, just save on the same path")
        path = self._git_path(name)
        blob = self.repository.peel(path)
        return File(BytesIO(blob.data), name=name)

    def _commit(self, message, tree):
        """Commit the given tree using this commit message.

            @param message: text message
            @param tree: tree id
            @return: commit id
        """
        self.repository.create_commit(
            self.repository.head.name,
            pygit2.Signature(app_config.AUTHOR[0], app_config.AUTHOR[1]),
            pygit2.Signature(app_config.COMMITTER[0], app_config.COMMITTER[1]),
            message,
            tree,
            [self.repository.head.target],
        )

    def _save(self, name, content):
        """Save the File content under the given path name.

            @param name: file path, relative to the repository root
            @param content: File content (temporary or in-memory file object)
            @return: the name under which the content was saved
        """
        path = self._git_path(name)
        if hasattr(content, 'temporary_file_path'):
            blob = self.repository.create_blob_fromdisk(content.temporary_file_path())
            content.close()
        else:
            blob = self.repository.create_blob(content.read())
        tree = self.repository.insert(path, blob)
        self._commit(app_config.SAVE_MESSAGE, tree)
        return name

    def delete(self, name):
        """Delete the blob at the given path name by committing a tree without it.

            @param: name: file path, relative to the repository root
        """
        path = self._git_path(name)
        tree = self.repository.remove(path)
        self._commit(app_config.DELETE_MESSAGE, tree)

    def get_available_name(self, name):
        """Always allow to overwrite an existing name.

            @param: name: file path, relative to the repository root
        """
        return self._git_path(name)

    def exists(self, name):
        """Search the given name in the repository.

            @param: name: file path, relative to the repository root
        """
        path = self._git_path(name)
        return path in self.repository.tree

    def listdir(self, path):
        """List the contents of the given path.

            @param: path: directory path, relative to the repository root
            @return: ([], []) directories and files
        """
        path = self._git_path(path)
        tree = self.repository.peel(path)
        directories, files = [], []
        for entry in tree:
            if entry.filemode in wrappers.GIT_FILEMODE_BLOB_KINDS:
                files.append(entry.name)
            elif entry.filemode == wrappers.GIT_FILEMODE_TREE:
                directories.append(entry.name)
        return directories, files

    def size(self, name):
        """Return the size of the blob at the given path name.

            @param: name: file path, relative to the repository root
        """
        path = self._git_path(name)
        blob = self.repository.peel(path)
        return blob.size

    def url(self, name):
        path = self._git_path(name)
        if self.base_url is None:
            raise ValueError("This file is not accessible via a URL.")
        return urljoin(self.base_url, filepath_to_uri(path))

    def is_dir(self, name):
        """Return if the given name is a directory (Git tree).

            @param: name: file path, relative to the repository root
        """
        path = self._git_path(name)
        return self.repository.is_tree(path)

    def is_file(self, name):
        """Return if the given name is a file (Git blob).

            @param: name: file path, relative to the repository root
        """
        path = self._git_path(name)
        return self.repository.is_blob(path)
