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
Wrappers with enhanced methods around pygit2 objects.
"""

import pygit2


class BlobWrapper(object):
    """A lazy blob object that only loads data on demand."""
    _blob = None

    def __init__(self, repository, id):
        self._repository = repository
        self.id = id
        self.hex = str(id)
        self.type = pygit2.GIT_OBJ_BLOB

    def _load_blob(self):
        if self._blob is None:
            self._blob = self.repository[self.id]
        return self._blob

    def __getattr__(self, item):
        blob = self._load_blob()
        return getattr(blob, item)


class Repository(pygit2.Repository):

    def __init__(self, *args):
        super().__init__(*args)
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

        if tree_entry.type == 'blob':
            return BlobWrapper(self, tree_entry.id)

        return self[tree_entry.id]
