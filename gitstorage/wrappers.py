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

"""
Wrappers with enhanced methods around pygit2 objects.

Intentionally not imported unicode_literals because pygit2 didn't.
"""

from __future__ import absolute_import, print_function

import datetime

import pygit2


EPOCH = datetime.datetime(1970, 1, 1)

GIT_FILEMODE_NEW = 0o0000000
GIT_FILEMODE_TREE = 0o0040000
GIT_FILEMODE_BLOB = 0o0100644
GIT_FILEMODE_BLOB_EXECUTABLE = 0o0100755
GIT_FILEMODE_LINK = 0o0120000
GIT_FILEMODE_COMMIT = 0o0160000

GIT_FILEMODE_BLOB_KINDS = (GIT_FILEMODE_BLOB,
                           GIT_FILEMODE_BLOB_EXECUTABLE)


class Repository(pygit2.Repository):

    def __init__(self, *args):
        super(Repository, self).__init__(*args)
        # Always load the index
        self.index.read_tree(self.head.tree.oid)

    def find_object(self, path):
        """Find a tree, blob, etc. by its path in the working directory.

            @param path: file path, relative to the repository root
        """
        # Fast path for blobs
        try:
            return self[self.index[path].oid]
        except KeyError:
            # Tree traversal
            tree = self.head.tree
            if not path:
                return tree
            segments = path.split("/")
            name = segments.pop()
            for segment in segments:
                tree = tree[segment].to_object()
            return tree[name].to_object()

    def insert(self, path, blob_oid):
        """Insert the blob at the given path name creating missing intermediate trees.

            @param path: file path, relative to the repository root
            @param blob_oid: the blob oid already created
            @return: new root tree oid to commit

            Credits to Nico von Geyso (cholin) for the original code: https://github.com/libgit2/pygit2/pull/88/files

            TODO git_index_add would probably do the job if I could add an in-memory entry.
        """
        root_tree_builder = self.TreeBuilder(self.head.tree)
        current_tree = self[self.head.tree.oid]

        # Create directories hierarchy from last to first
        segments = path.split("/")
        name = segments.pop()
        segments.reverse()

        # Search for existing trees in path
        tree_stack = [("/", root_tree_builder)]
        while segments:
            if segments[-1] not in current_tree:
                # Found where to begin adding new objects
                break
            segment = segments.pop()  # Remember path is reversed
            current_tree = self[current_tree[segment].oid]
            # Append a draft version of the new tree
            tree_stack.append((segment, self.TreeBuilder(current_tree.oid)))

        # Insert blob
        if segments:
            # Insert the blob in a new tree that we'll attach later
            parent_tree_builder = self.TreeBuilder()
        else:
            # Insert the blob in the existing tree
            parent_tree_builder = tree_stack[-1][1]
        parent_tree_builder.insert(name, blob_oid, GIT_FILEMODE_BLOB)
        current_tree_oid = parent_tree_builder.write()

        # Now create missing intermediate trees
        size = len(segments)
        for i, segment in enumerate(segments):
            if i < (size - 1):
                # Create a parent tree builder to insert our new tree
                parent_tree_builder = self.TreeBuilder()
                parent_tree_builder.insert(segment, current_tree_oid, GIT_FILEMODE_TREE)
                # Now the parent is the current tree
                current_tree_oid = parent_tree_builder.write()
            else:
                # This is the segment to insert at the root tree
                tree_stack.append((segment, None))

        # Connect the created trees from the deepest existing tree and up to the root
        child_segment = tree_stack.pop()[0]
        tree_stack.reverse()
        for segment, tree_builder in tree_stack:
            tree_builder.insert(child_segment, current_tree_oid, GIT_FILEMODE_TREE)
            current_tree_oid = tree_builder.write()
            child_segment = segment

        # Reload the index
        self.index.read_tree(current_tree_oid)

        # We are now back to the root tree but updated
        return current_tree_oid

    def remove(self, path):
        """Remove the given path from the repository tree.

            @param path: file path, relative to the repository root
            @return: new root tree oid to commit

            TODO git_index_remove would probably do the job if I could add an in-memory entry.
        """
        root_tree_builder = self.TreeBuilder(self.head.tree)
        current_tree = self[self.head.tree.oid]

        segments = path.split("/")
        name = segments.pop()
        segments.reverse()

        # Build up draft trees all the way down
        tree_stack = [("/", root_tree_builder)]
        while segments:
            segment = segments.pop()  # Remember path is reversed
            current_tree = self[current_tree[segment].oid]
            tree_stack.append((segment, self.TreeBuilder(current_tree.oid)))

        # Remove the blob
        child_segment, tmp_tree_builder = tree_stack.pop()
        tmp_tree_builder.remove(name)
        current_tree_oid = tmp_tree_builder.write()
        current_tree = self[current_tree_oid]

        # Write the draft trees from the deepest up to the root, removing empty trees afterwards
        tree_stack.reverse()
        for segment, tree_builder in tree_stack:
            if not len(current_tree):
                tree_builder.remove(child_segment)
            current_tree_oid = tree_builder.write()
            current_tree = self[current_tree_oid]
            child_segment = segment

        # Reload the index
        self.index.read_tree(current_tree_oid)

        # We are now back to the root tree but updated
        return current_tree_oid

    def is_tree(self, path):
        obj = self.find_object(path)
        return obj.type is pygit2.GIT_OBJ_TREE

    def is_blob(self, path):
        obj = self.find_object(path)
        return obj.type is pygit2.GIT_OBJ_BLOB
