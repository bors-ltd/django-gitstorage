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

"""
Repository automatically opening the path configured in settings, with enhanced methods.
"""

import pygit2

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class Repository(pygit2.Repository):

    def __init__(self, *args, **kwargs):
        try:
            path = settings.GITSTORAGE_REPOSITORY
        except AttributeError:
            raise ImproperlyConfigured("GITSTORAGE_REPOSITORY is required")
        super().__init__(path, *args, **kwargs)
        # Not strictly required but sane, gitstorage is not designed for checkouts
        assert self.is_bare
        # Always load the index
        self.index.read_tree(self.tree.id)

    @property
    def commit(self):
        """shortcut to the head commit"""
        return self.head.peel(pygit2.GIT_OBJ_COMMIT)

    @property
    def tree(self):
        """shortcut to the head tree"""
        return self.head.peel(pygit2.GIT_OBJ_TREE)

    def open(self, path):
        """High-level object retriever.

            @param path: object path, relative to the repository root
        """

        # Repository root
        if path in ("", "/"):
            return self.tree

        tree_entry = self.tree[path]
        return self[tree_entry.id]

    def listdir(self, path):
        """List the contents of the given path.

            @param: path: tree path, relative to the repository root
            @return: ([], []) trees and blobs

        Contrary to a filesystem listdir, we expose tree entries, and keep the notion of blobs and trees.
        """
        tree = self.open(path)
        trees, blobs = [], []
        for entry in tree:
            if entry.type == "blob":
                blobs.append(entry)
            elif entry.type == "tree":
                trees.append(entry)
        return trees, blobs
