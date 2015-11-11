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


GIT_FILEMODE_NEW = 0o0000000
GIT_FILEMODE_TREE = 0o0040000
GIT_FILEMODE_BLOB = 0o0100644
GIT_FILEMODE_BLOB_EXECUTABLE = 0o0100755
GIT_FILEMODE_LINK = 0o0120000
GIT_FILEMODE_COMMIT = 0o0160000

GIT_FILEMODE_BLOB_KINDS = (
    GIT_FILEMODE_BLOB,
    GIT_FILEMODE_BLOB_EXECUTABLE,
)


class Repository(pygit2.Repository):

    def __init__(self, *args):
        super(Repository, self).__init__(*args)
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

            @param path: file path, relative to the repository root
        """

        # Repository root
        if path in ("", "/"):
            return self.tree

        tree_entry = self.tree[path]
        return self[tree_entry.id]

    def insert(self, path, blob_oid):
        """Insert the blob at the given path name creating missing intermediate trees.

            @param path: file path, relative to the repository root
            @param blob_oid: the blob id already created
            @return: new root tree id to commit

            Credits to Nico von Geyso (cholin) for the original code: https://github.com/libgit2/pygit2/pull/88/files

            TODO git_index_add would probably do the job if I could add an in-memory entry.
        """
        root_tree_builder = self.TreeBuilder(self.tree)
        current_tree = self.tree

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
            current_tree = self[current_tree[segment].id]
            # Append a draft version of the new tree
            tree_stack.append((segment, self.TreeBuilder(current_tree.id)))

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
            @return: new root tree id to commit

            TODO git_index_remove would probably do the job if I could add an in-memory entry.
        """
        root_tree_builder = self.TreeBuilder(self.tree)
        current_tree = self.tree

        segments = path.split("/")
        name = segments.pop()
        segments.reverse()

        # Build up draft trees all the way down
        tree_stack = [("/", root_tree_builder)]
        while segments:
            segment = segments.pop()  # Remember path is reversed
            current_tree = self[current_tree[segment].id]
            tree_stack.append((segment, self.TreeBuilder(current_tree.id)))

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
        tree_entry = self.tree[path]
        return tree_entry.type == "tree"

    def is_blob(self, path):
        tree_entry = self.tree[path]
        return tree_entry.type == "blob"
