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
import pygit2

from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse
from django.http.response import Http404
from django.test import TestCase
from django.test.client import RequestFactory

from gitstorage import factories
from gitstorage import models
from gitstorage import storage
from gitstorage.utils import Path
from gitstorage.tests.utils import VanillaRepositoryMixin

from . import views


class BaseViewTestCase(VanillaRepositoryMixin, TestCase):
    path = None

    def setUp(self):
        super().setUp()
        self.storage = storage.GitStorage(self.location)

        if self.path is None:
            raise ValueError("Forgot to declare a path!")

        self.path = Path(self.path)
        self.user = factories.UserFactory(password="password")
        self.client.login(username=self.user.username, password="password")

        git_obj = self.storage.repository.open(self.path)

        if git_obj.type == pygit2.GIT_OBJ_BLOB:
            self.blob = git_obj

            # Permission to parent path
            parent = Path(self.path.parent_path)
            self.permission = factories.TreePermissionFactory(
                parent_path=parent.parent_path, name=parent.name, user=self.user
            )

            # Blob metadata
            self.metadata = factories.BlobMetadataFactory(id=self.blob.hex, mimetype="text/plain")

        elif git_obj.type == pygit2.GIT_OBJ_TREE:
            self.tree = git_obj

            # Permission to itself
            factories.TreePermissionFactory(parent_path=self.path.parent_path, name=self.path.name, user=self.user)


class PreviewViewTestCase(BaseViewTestCase):
    path = "path/with/unicode/de\u0301po\u0302t.txt"

    def test_get(self):
        response = self.client.get(reverse('blob_preview', args=[self.path]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], "inline; filename=dépôt.txt")
        self.assertContains(response, "de\u0301po\u0302t")


class DownloadViewTestCase(BaseViewTestCase):
    path = "path/with/unicode/de\u0301po\u0302t.txt"

    def test_get(self):
        response = self.client.get(reverse('blob_download', args=[self.path]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Disposition'], "attachment; filename=dépôt.txt")
        self.assertContains(response, "de\u0301po\u0302t")


class DeleteViewTestCase(BaseViewTestCase):
    path = "foo/bar/baz/qux.txt"

    def test_get(self):
        response = self.client.get(reverse('blob_delete', args=[self.path]))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(reverse('blob_delete', args=[self.path]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.storage.exists(self.path))


class UploadViewTestCase(BaseViewTestCase):
    path = "foo/bar/baz"

    def setUp(self):
        super().setUp()
        # A blob found in the path
        self.blob = self.storage.repository.open("foo/bar/baz/qux.txt")
        self.blob_metadata = factories.BlobMetadataFactory(id=self.blob.hex)

    def test_get(self):
        response = self.client.get(reverse('tree_upload', args=[self.path]))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        response = self.client.post(reverse('tree_upload', args=[self.path]))
        self.assertEqual(response.status_code, 200)

        data = {'file': SimpleUploadedFile("toto.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF")}
        response = self.client.post(reverse('tree_upload', args=[self.path]), data=data)
        self.assertEqual(response.status_code, 302)

        blob = self.storage.repository.open("foo/bar/baz/toto.jpg")
        self.assertTrue(models.BlobMetadata.objects.filter(id=blob.hex, mimetype="image/jpeg").exists())


class SharesViewTestCase(BaseViewTestCase):
    path = "foo/bar/baz"

    def test_get(self):
        response = self.client.get(reverse('tree_shares', args=[self.path]))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        user = factories.UserFactory()
        factories.TreePermissionFactory(parent_path=self.path.parent_path, name=self.path.name, user=user)

        response = self.client.post(reverse('tree_shares', args=[self.path]))
        self.assertEqual(response.status_code, 200)

        data = {'users': user.pk}
        response = self.client.post(reverse('tree_shares', args=[self.path]), data=data)
        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            models.TreePermission.objects.filter(parent_path="foo/bar", name="baz", user=user).exists()
        )

        # Re-remove the same
        response = self.client.post(reverse('tree_shares', args=[self.path]), data=data)
        self.assertEqual(response.status_code, 200)


class ShareViewTestCase(BaseViewTestCase):
    path = "foo/bar/baz"

    def test_get(self):
        response = self.client.get(reverse('tree_share', args=[self.path]))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        user = factories.UserFactory()

        response = self.client.post(reverse('tree_share', args=[self.path]))
        self.assertEqual(response.status_code, 200)

        self.assertFalse(models.TreePermission.objects.filter(parent_path="foo/bar", name="baz", user=user).exists())

        data = {'users': user.pk}
        response = self.client.post(reverse('tree_share', args=[self.path]), data=data)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(models.TreePermission.objects.filter(parent_path="foo/bar", name="baz", user=user).exists())

        # Re-add the same
        response = self.client.post(reverse('tree_share', args=[self.path]), data=data)
        self.assertEqual(response.status_code, 200)


class BlobViewTestCase(BaseViewTestCase):
    path = "foo/bar/baz/qux.txt"

    def test_object_type(self):
        view = views.TestBlobView(object=self.blob)
        self.assertIsNone(view.check_object_type())
        view.allowed_types = ()
        self.assertRaises(Http404, view.check_object_type)

    def test_get_context_data(self):
        self.maxDiff = None

        response = self.client.get(reverse('repo_browse', args=[self.path]))
        context = response.context
        self.assertEqual(context['path'], self.path)
        self.assertEqual(context['object'].id, self.blob.id)
        self.assertEqual(context['metadata'].id, self.metadata.id)
        self.assertEqual(list(context['root_trees']), [])  # No permission on root
        self.assertEqual(context['breadcrumbs'], ["foo", "foo/bar", "foo/bar/baz", "foo/bar/baz/qux.txt"])

    def test_get_hidden(self):
        response = self.client.get(reverse('repo_browse', args=["path/with/hidden/.file"]))
        self.assertEqual(response.status_code, 403)

    def test_get_unknown(self):
        response = self.client.get(reverse('repo_browse', args=["toto/coin"]))
        self.assertEqual(response.status_code, 404)

    def test_check_permissions(self):
        response = self.client.get(reverse('repo_browse', args=[self.path]))
        self.assertEqual(response.status_code, 200)

        user = factories.UserFactory(password="password")
        self.client.login(username=user.username, password="password")
        response = self.client.get(reverse('repo_browse', args=[self.path]))
        self.assertEqual(response.status_code, 403)

        tree_path = Path(self.path.parent_path)
        factories.TreePermissionFactory(parent_path=tree_path.parent_path, name=tree_path.name, user=user)
        response = self.client.get(reverse('repo_browse', args=[self.path]))
        self.assertEqual(response.status_code, 200)


class TreeViewTestCase(BaseViewTestCase):
    path = "foo/bar/baz"

    def setUp(self):
        super().setUp()
        # A blob found in the path
        self.blob = self.storage.repository.open("foo/bar/baz/qux.txt")
        self.blob_metadata = factories.BlobMetadataFactory(id=self.blob.hex)

    def test_object_type(self):
        view = views.TestTreeView(object=self.tree)
        self.assertIsNone(view.check_object_type())
        view.allowed_types = ()
        self.assertRaises(Http404, view.check_object_type)

    def test_get_context_data(self):
        self.maxDiff = None

        response = self.client.get(reverse('repo_browse', args=[self.path]))
        context = response.context
        self.assertEqual(context['path'], self.path)
        self.assertEqual(context['object'].hex, self.tree.hex)
        self.assertEqual(context['metadata'].id, self.tree.hex)
        self.assertEqual(context['root_trees'], [])  # No permission on root
        self.assertEqual(context['breadcrumbs'], ["foo", "foo/bar", "foo/bar/baz"])
        self.assertEqual(context['trees'], [])
        self.assertEqual(
            context['blobs'],
            [
                {
                    'name': "qux.txt",
                    'path': "foo/bar/baz/qux.txt",
                    'metadata': self.blob_metadata,
                }
            ]
        )

    def test_get_hidden(self):
        response = self.client.get(reverse('repo_browse', args=["path/with/hidden/.directory"]))
        self.assertEqual(response.status_code, 403)

    def test_get_unknown(self):
        response = self.client.get(reverse('repo_browse', args=["toto/coin"]))
        self.assertEqual(response.status_code, 404)

    def test_check_permissions(self):
        response = self.client.get(reverse('repo_browse', args=[self.path]))
        self.assertEqual(response.status_code, 200)

        user = factories.UserFactory(password="password")
        self.client.login(username=user.username, password="password")
        response = self.client.get(reverse('repo_browse', args=[self.path]))
        self.assertEqual(response.status_code, 403)

        factories.TreePermissionFactory(parent_path=self.path.parent_path, name=self.path.name, user=user)
        response = self.client.get(reverse('repo_browse', args=[self.path]))
        self.assertEqual(response.status_code, 200)


class AdminPermissionTestCase(BaseViewTestCase):
    path = ""

    def setUp(self):
        super().setUp()
        # A blob found at the root
        self.blob = self.storage.repository.open("foo.txt")
        self.blob_metadata = factories.BlobMetadataFactory(id=self.blob.hex)

    def test_check_permission(self):
        user = factories.UserFactory(password="pass1")
        self.client.login(username=user.username, password="pass1")
        response = self.client.get(reverse('repo_browse', args=[""]))
        self.assertEqual(response.status_code, 403)

        superuser = factories.SuperUserFactory(password="pass2")
        self.client.login(username=superuser.username, password="pass2")
        response = self.client.get(reverse('repo_browse', args=[""]))
        self.assertEqual(response.status_code, 200)


class CoverageTestCase(VanillaRepositoryMixin, TestCase):
    """Edge cases to reach 100 % coverage."""

    def setUp(self):
        super().setUp()
        self.storage = storage.GitStorage(self.location)

    def test_initkwargs(self):
        self.assertRaises(TypeError, views.DummyRepositoryView.as_view, get=None)
        self.assertRaises(TypeError, views.DummyRepositoryView.as_view, foo=None)

    def test_view_path(self):
        request = RequestFactory()
        view = views.DummyRepositoryView.as_view()
        # These paths exist
        self.assertRaises(Http404, view, request, "foo.txt;download")
        self.assertRaises(Http404, view, request, "foo/bar/baz/qux.txt/;download")

    def test_type_to_view(self):
        request = RequestFactory()
        view = views.DummyRepositoryView.as_view()
        # These paths exist
        self.assertRaises(PermissionDenied, view, request, "foo/bar/baz")
        self.assertRaises(PermissionDenied, view, request, "foo/bar/baz/qux.txt")

    def test_check_permissions(self):
        view = views.DummyRepositoryView()
        self.assertRaises(NotImplementedError, view.check_permissions)

        request = RequestFactory()
        request.user = factories.UserFactory()
        view = views.DummyAdminDeleteView(request=request, path=Path(""))
        self.assertRaises(PermissionDenied, view.check_permissions)

        request = RequestFactory()
        request.user = factories.SuperUserFactory()
        view = views.DummyAdminDeleteView(request=request, path=Path(""))
        self.assertIsNone(view.check_permissions())

    def test_filter_hidden(self):
        request = RequestFactory()
        request.user = factories.UserFactory()
        view = views.DummyTreeView(request=request, path=Path("path/with/hidden"), storage=self.storage)

        blobs = view.filter_blobs()
        self.assertNotIn(".file", [entry['name'] for entry in blobs])

        trees = view.filter_trees(view.path)
        self.assertNotIn(".directory", [entry['name'] for entry in trees])

    def test_dispatch_not_found(self):
        request = RequestFactory()
        request.user = factories.UserFactory()
        view = views.DummyTreeView()
        self.assertRaises(Http404, view.dispatch, request, path=Path("tot/coin"))
