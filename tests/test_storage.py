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

from os import path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.core.files.uploadedfile import SimpleUploadedFile, TemporaryUploadedFile
from django.test import TestCase

from gitstorage import factories
from gitstorage.storage import GitStorage
from gitstorage.tests.utils import NewRepositoryMixin, VanillaRepositoryMixin


def ls_tree(tree):
    return [tree_entry.name for tree_entry in tree]


class NewGitStorageTestCase(NewRepositoryMixin, TestCase):
    """Tests with an empty repository from scratch."""

    def setUp(self):
        super().setUp()
        self.storage = GitStorage(location=self.location)

    def test_init_repository(self):
        repository = self.storage.repository
        self.assertTrue(path.exists(self.location))
        self.assertEqual(self.storage.location, self.location)
        self.assertIsNotNone(repository.commit)
        self.assertEqual(['refs/heads/master'], repository.listall_references())  # apps default

        # Introspect commit
        commit = repository.commit
        self.assertEqual("Initial commit by Git Storage", commit.message)

    def test_path_root(self):
        name = "foo.txt"
        path = self.storage._git_path(name)
        self.assertEqual(name, path)

    def test_path_subtree(self):
        name = "foo/bar/baz/qux.txt"
        path = self.storage._git_path(name)
        self.assertEqual(name, path)

    def test_outside_path(self):
        for name in ("/foo/bar/baz/qux.txt",
                     "../foo/bar/baz/qux.txt",
                     "foo/../../bar/baz/qux.txt"):
            self.assertRaises(SuspiciousOperation, self.storage._git_path, name)

    def test_save_root(self):
        name = "foo.txt"
        content = SimpleUploadedFile(name, b'foo')
        ret = self.storage.save(name, content)
        self.assertEqual(name, ret)

        # Introspect commit
        commit = self.storage.repository.commit
        self.assertEqual("Saved by Git Storage", commit.message)
        tree = commit.tree
        self.assertEqual([name], ls_tree(tree))
        blob = self.storage.repository[tree[name].id]
        self.assertEqual(b"foo", blob.data)

    def test_save_subtree(self):
        name = "foo/bar/baz/qux.txt"
        content = SimpleUploadedFile(name, b'qux')
        ret = self.storage.save(name, content)
        self.assertEqual(name, ret)

        # Introspect commit
        tree = self.storage.repository.open("foo/bar/baz")
        self.assertEqual(["qux.txt"], ls_tree(tree))
        blob = self.storage.repository[tree["qux.txt"].id]
        self.assertEqual(b"qux", blob.data)

    def test_open_unknown(self):
        self.assertRaises(KeyError, self.storage._open, "foo/bar/baz/toto")

    def test_get_available_name(self):
        self.assertEqual(self.storage.get_available_name("my/path"), "my/path")

    def test_exists_unknown(self):
        self.assertFalse(self.storage.exists("foo.txt"))
        self.assertFalse(self.storage.exists("foo/bar/baz/qux.txt"))

    def test_listdir_unknown(self):
        self.assertRaises(KeyError, self.storage.listdir, "foo/bar/baz/toto")

    def test_size_unknown(self):
        self.assertRaises(KeyError, self.storage.size, "foo/bar/baz/toto")


class MissingSettingsTestCase(TestCase):

    def test_missing_settings(self):
        self.assertRaises(ImproperlyConfigured, GitStorage)


class VanillaGitStorageTestCase(VanillaRepositoryMixin, TestCase):
    """Tests with an existing and pre-filled repository."""

    def setUp(self):
        super().setUp()
        settings.GIT_STORAGE_URL = None
        self.storage = GitStorage()

    def test_init_repository(self):
        """Open an existing repository (created by git for reference)."""
        repository = self.storage.repository
        self.assertEqual(self.storage.location, self.location)
        self.assertEqual('d104ab48cc867e89928e0094d192e5516a98dd25', repository.commit.hex)
        self.assertEqual(['refs/heads/master'], repository.listall_references())  # apps default

    def test_path(self):
        """Make coverage happy."""
        self.assertRaises(NotImplementedError, self.storage.path, "foo.txt")

    def test_open_root(self):
        """Open a blob at the root of the repository."""
        blob = self.storage.open("foo.txt")
        self.assertEqual("foo.txt", blob.name)
        self.assertEqual(b"foo\n", blob.read())

    def test_open_subtree(self):
        """Open a blob in a subtree."""
        blob = self.storage.open("foo/bar/baz/qux.txt")
        self.assertEqual("foo/bar/baz/qux.txt", blob.name)
        self.assertEqual(b"qux\n", blob.read())

    def test_open_write(self):
        self.assertRaises(ImproperlyConfigured, self.storage._open, "foo.txt", mode='wb')

    def test_overwrite_root(self):
        name = "foo.txt"
        self.storage.save(name, SimpleUploadedFile(name, b'toto'))

        content = self.storage.open(name)
        self.assertEqual(b"toto", content.read())

    def test_overwrite_subtree(self):
        name = "foo/bar/baz/qux.txt"
        self.storage.save(name, SimpleUploadedFile(name, b'toto'))

        content = self.storage.open(name)
        self.assertEqual(b"toto", content.read())

    def test_save_existing_subtree(self):
        name = "foo/bar/toto.txt"
        self.storage.save(name, SimpleUploadedFile(name, b'toto'))

        # Introspect commit
        commit = self.storage.repository.commit
        tree = commit.tree
        self.assertEqual(["foo.txt", "foo", "path"], ls_tree(tree))

        # "foo/"
        tree = self.storage.repository[tree["foo"].id]
        self.assertEqual(["bar"], ls_tree(tree))

        # "foo/bar/"
        tree = self.storage.repository[tree["bar"].id]
        self.assertEqual(["baz", "toto.txt"], ls_tree(tree))

        # "foo/bar/baz"
        tree = self.storage.repository[tree["baz"].id]
        self.assertEqual(["qux.txt"], ls_tree(tree))

    def test_save_temporary_file(self):
        name = "foo/bar/toto.txt"
        content = TemporaryUploadedFile("temporary", "application/binary", (settings.FILE_UPLOAD_MAX_MEMORY_SIZE + 1),
                                        None)
        self.storage.save(name, content)
        self.assertEqual(self.storage.open(name).read(), b'')

    def test_delete_root(self):
        name = "foo.txt"
        self.storage.delete(name)

        # Introspect commit
        commit = self.storage.repository.commit
        self.assertEqual("Deleted by Git Storage", commit.message)
        tree = commit.tree
        self.assertEqual(["foo", "path"], ls_tree(tree))

    def test_delete_subtree(self):
        name = "foo/bar/baz/qux.txt"
        self.storage.delete(name)

        # Introspect commit
        commit = self.storage.repository.commit
        tree = commit.tree
        # Empty tree removed
        self.assertEqual(["foo.txt", "path"], ls_tree(tree))

    def test_exists(self):
        self.assertTrue(self.storage.exists("foo.txt"))
        self.assertTrue(self.storage.exists("foo/bar/baz/qux.txt"))

    def test_listdir_root(self):
        trees, blobs = self.storage.listdir(".")
        self.assertEqual([te.name for te in trees], ["foo", "path"])
        self.assertEqual([te.name for te in blobs], ["foo.txt"])

    def test_listdir_subtree(self):
        trees, blobs = self.storage.listdir("foo/bar/baz")
        self.assertEqual(trees, [])
        self.assertEqual([te.name for te in blobs], ["qux.txt"])

    def test_size_root(self):
        self.assertEqual(4, self.storage.size("foo.txt"))

    def test_size_subtree(self):
        self.assertEqual(4, self.storage.size("foo/bar/baz/qux.txt"))

    def test_size_tree(self):
        self.assertRaises(AttributeError, self.storage.size, "foo/bar/baz")

    def test_url(self):
        self.assertRaises(ValueError, self.storage.url, "foo/bar/baz")
        self.storage = GitStorage(base_url="/mystorage/")
        self.assertEqual(self.storage.url("foo/bar/baz"), "/mystorage/foo/bar/baz")
        self.assertEqual(self.storage.url("foo/bar/baz/qux.txt"), "/mystorage/foo/bar/baz/qux.txt")

    def test_set_author(self):
        user = factories.UserFactory(first_name="John", last_name="Doe", email="john.doe@example.com")

        self.storage.save("toto.txt", SimpleUploadedFile("toto.txt", b'toto'))
        commit = self.storage.repository.commit

        self.assertEqual(commit.author.name, "Git Storage")
        self.assertEqual(commit.author.email, "git@storage")

        self.storage.set_author(user)

        self.storage.save("toto.txt", SimpleUploadedFile("toto.txt", b'toto'))
        commit = self.storage.repository.commit

        self.assertEqual(commit.author.name, "John Doe")
        self.assertEqual(commit.author.email, "john.doe@example.com")
