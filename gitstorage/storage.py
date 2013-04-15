# -*- coding: utf-8 -*-
# Copyright 2013 Bors Ltd
#This file is part of GitStorage.
#
#    GitStorage is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Foobar is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import absolute_import, print_function, unicode_literals

from cStringIO import StringIO
import os
try:
    from urllib.parse import urljoin
except ImportError:     # Python 2
    from urlparse import urljoin

from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files import storage, File
from django.conf import settings
from django.utils import timezone
from django.utils.encoding import filepath_to_uri
from django.utils._os import safe_join, abspathu

import pygit2

from . import utils
from . import wrappers


DEFAULT_REFERENCE = 'refs/heads/master'
DEFAULT_AUTHOR = ("Git Storage", "git@storage")
INITIAL_COMMIT_MESSAGE = "Initial commit by Git Storage"
DEFAULT_SAVE_MESSAGE = "Saved by Git Storage"
DEFAULT_DELETE_MESSAGE = "Deleted by Git Storage"

# Always encode tree entry names to UTF-8
GIT_FILESYSTEM_ENCODING = 'utf8'


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

        # Reference (head)
        try:
            self.reference = settings.GIT_STORAGE_REFERENCE
        except AttributeError:
            self.reference = DEFAULT_REFERENCE

        # Author
        try:
            self.author_name, self.author_email = settings.GIT_STORAGE_AUTHOR
        except AttributeError:
            self.author_name, self.author_email = DEFAULT_AUTHOR

        # Committer
        try:
            self.committer_name, self.committer_email = settings.GIT_STORAGE_COMMITTER
        except AttributeError:
            self.committer_name, self.committer_email = DEFAULT_AUTHOR

        # Save message
        try:
            self.save_message = settings.GIT_STORAGE_SAVE_MESSAGE
        except AttributeError:
            self.save_message = DEFAULT_SAVE_MESSAGE

        # Delete message
        try:
            self.delete_message = settings.GIT_STORAGE_DELETE_MESSAGE
        except AttributeError:
            self.delete_message = DEFAULT_DELETE_MESSAGE

        # Create repository
        if not os.path.exists(location):
            repository = pygit2.init_repository(self.location, True)  # Bare
            # Initial commit
            author = utils.make_signature(self.author_name, self.author_email)
            committer = utils.make_signature(self.committer_name, self.committer_email)
            tree = repository.TreeBuilder().write()
            repository.create_commit(self.reference,
                                     author,
                                     committer,
                                     INITIAL_COMMIT_MESSAGE,
                                     tree,
                                     [])
            del repository

        # Open our repository instance
        self.repository = wrappers.Repository(self.location)
        assert self.repository.status() == {}, "Repository must be clean"

    def _git_path(self, name):
        """Clean path name and make it relative to the repository root.

         Taken from FileSystemStorage.path.

            @param name: file path, relative to the repository root
            @return: cleaned path
        """
        try:
            path = safe_join(self.location, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)
        path = os.path.normpath(path)
        # Strip off the repo absolute path
        path = path[len(self.location) + 1:]
        # PyGit2 still uses bytestrings for filesystem paths on Python 2
        return path.encode(GIT_FILESYSTEM_ENCODING)

    def _open(self, name, mode='rb'):
        """Open the given file name, always in 'rb' mode.

            @param: name: file path, relative to the repository root
            @return: File object
        """
        if mode != 'rb':
            raise ImproperlyConfigured("Can't rewrite Git files, just save on the same path")
        path = self._git_path(name)
        blob = self.repository.find_object(path)
        return File(StringIO(blob.data), name=name)

    def _save(self, name, content):
        """Save the File content under the given path name.

            @param name: file path, relative to the repository root
            @param content: File content (temporary or in-memory file object)
            @return: the name under which the content was saved
        """
        path = self._git_path(name)
        if hasattr(content, 'temporary_file_path'):
            blob = self.repository.create_blob_fromfile(content.temporary_file_path())
            content.close()
        else:
            blob = self.repository.create_blob(content.read())
        tree = self.repository.insert(path, blob)
        self._commit(self.save_message, tree)
        return name

    def _commit(self, message, tree):
        """Commit the given tree using this commit message.

            @param message: unicode message
            @param tree: tree oid
            @return: commit oid
        """
        tz = timezone.get_current_timezone()
        self.repository.create_commit(self.reference,
                                      utils.make_signature(self.author_name, self.author_email, tz=tz),
                                      utils.make_signature(self.committer_name, self.committer_email, tz=tz),
                                      message,
                                      tree,
                                      [self.repository.head.oid])

    def delete(self, name):
        """Delete the blob at the given path name by committing a tree without it.

            @param: name: file path, relative to the repository root
        """
        path = self._git_path(name)
        tree = self.repository.remove(path)
        self._commit(self.delete_message, tree)

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
        try:
            self.repository.find_object(path)
        except KeyError:
            return False
        return True

    def listdir(self, path):
        """List the contents of the given path.

            @param: path: directory path, relative to the repository root
            @return: ([], []) directories and files
        """
        path = self._git_path(path)
        tree = self.repository.find_object(path)
        directories, files = [], []
        for entry in tree:
            if entry.attributes in wrappers.GIT_FILEMODE_BLOB_KINDS:
                files.append(entry.name.decode(GIT_FILESYSTEM_ENCODING))
            elif entry.attributes == wrappers.GIT_FILEMODE_TREE:
                directories.append(entry.name.decode(GIT_FILESYSTEM_ENCODING))
        return directories, files

    def size(self, name):
        """Return the size of the blob at the given path name.

            @param: name: file path, relative to the repository root
        """
        path = self._git_path(name)
        blob = self.repository.find_object(path)
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
