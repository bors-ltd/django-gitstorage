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
        return self[tree_entry.id]
