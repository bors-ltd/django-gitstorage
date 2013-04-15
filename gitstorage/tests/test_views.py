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

import types

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http.response import Http404
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

import pygit2

from . import factories
from . import views
from .utils import VanillaRepositoryMixin
from .. import models
from .. import storage
from ..utils import Path


class PreviewViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(PreviewViewTestCase, self).setUp()
        self.storage = storage.GitStorage(self.location)
        self.view = views.TestPreviewView()
        self.view.storage = self.storage
        self.view.path = Path("foo/bar/baz/qux.txt")
        self.view.object = self.storage.repository.find_object(self.view.path)
        self.view.metadata = factories.BlobMetadataFactory(oid=self.view.object.hex, mimetype="text/plain")

    def test_preview(self):
        self.view.request = RequestFactory().get(self.view.path)
        response = self.view.get(self.view.request)
        self.assertEqual(response['Content-Disposition'], "inline; filename=qux.txt")
        self.assertContains(response, "qux")


class DownloadViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(DownloadViewTestCase, self).setUp()
        self.storage = storage.GitStorage(self.location)
        self.view = views.TestDownloadView()
        self.view.storage = self.storage
        self.view.path = Path("foo/bar/baz/qux.txt")
        self.view.object = self.storage.repository.find_object(self.view.path)
        self.view.metadata = factories.BlobMetadataFactory(oid=self.view.object.hex, mimetype="text/plain")

    def test_download(self):
        self.view.request = RequestFactory().get(self.view.path)
        response = self.view.get(self.view.request)
        self.assertEqual(response['Content-Disposition'], "attachment; filename=qux.txt")
        self.assertContains(response, "qux")


class DeleteViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(DeleteViewTestCase, self).setUp()
        self.storage = storage.GitStorage(self.location)
        self.view = views.TestDeleteView()
        self.view.storage = self.storage
        self.view.path = Path("foo/bar/baz/qux.txt")
        self.view.object = self.storage.repository.find_object(self.view.path)
        self.view.metadata = factories.BlobMetadataFactory(oid=self.view.object.hex, mimetype="text/plain")

    def test_delete(self):
        self.view.request = RequestFactory().post(self.view.path)
        response = self.view.post(self.view.request)
        self.assertIsNone(response)
        self.assertFalse(self.storage.exists("foo/bar/baz/qux.txt"))


class UploadViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(UploadViewTestCase, self).setUp()
        self.storage = storage.GitStorage(self.location)
        self.view = views.TestUploadView()
        self.view.storage = self.storage
        self.view.path = Path("foo/bar/baz")
        self.view.object = self.storage.repository.find_object(self.view.path)

    def test_upload(self):
        self.view.request = RequestFactory().post(self.view.path)
        response = self.view.post(self.view.request)
        self.assertContains(response, "invalid")

        data = {'file': SimpleUploadedFile("toto.jpg", b"toto")}
        self.view.request = RequestFactory().post(self.view.path, data=data)
        response = self.view.post(self.view.request)
        self.assertEqual(response['Location'], "/success/")

        blob = self.storage.repository.find_object("foo/bar/baz/toto.jpg")
        self.assertTrue(models.BlobMetadata.objects.filter(oid=blob.hex, mimetype="image/jpeg").exists())


class SharesViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(SharesViewTestCase, self).setUp()
        self.storage = storage.GitStorage(self.location)
        self.view = views.TestSharesView()
        self.view.storage = self.storage
        self.view.path = Path("foo/bar/baz")
        self.view.object = self.storage.repository.find_object(self.view.path)

    def test_get(self):
        self.user = factories.SuperUserFactory()
        factories.TreePermissionFactory(parent_path="foo/bar", name="baz", user=self.user)

        self.view.request = RequestFactory().get(self.view.path)
        response = self.view.get(self.view.request)
        self.assertContains(response, "shares")

    def test_post(self):
        self.user = factories.UserFactory()
        factories.TreePermissionFactory(parent_path="foo/bar", name="baz", user=self.user)

        self.view.request = RequestFactory().post(self.view.path)
        response = self.view.post(self.view.request)
        self.assertContains(response, "invalid")


        data = {'users': self.user.pk}
        self.view.request = RequestFactory().post(self.view.path,  data=data)
        response = self.view.post(self.view.request)
        self.assertEqual(response['Location'], "/success/")

        self.assertFalse(
            models.TreePermission.objects.filter(parent_path="foo/bar", name="baz", user=self.user).exists())

        # Re-remove the same
        response = self.view.post(self.view.request)
        self.assertContains(response, "invalid")


class ShareViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(ShareViewTestCase, self).setUp()
        self.storage = storage.GitStorage(self.location)
        self.view = views.TestShareView()
        self.view.storage = self.storage
        self.view.path = Path("foo/bar/baz")
        self.view.object = self.storage.repository.find_object(self.view.path)

    def test_get(self):
        self.user = factories.SuperUserFactory()

        self.view.request = RequestFactory().get(self.view.path)
        response = self.view.get(self.view.request)
        self.assertContains(response, "share")

    def test_post(self):
        self.user = factories.UserFactory()

        self.view.request = RequestFactory().post(self.view.path)
        response = self.view.post(self.view.request)
        self.assertContains(response, "invalid")

        data = {'users': self.user.pk}
        self.view.request = RequestFactory().post(self.view.path,  data=data)
        response = self.view.post(self.view.request)
        self.assertEqual(response['Location'], "/success/")

        self.assertTrue(
            models.TreePermission.objects.filter(parent_path="foo/bar", name="baz", user=self.user).exists())

        # Re-add the same
        response = self.view.post(self.view.request)
        self.assertContains(response, "invalid")


@override_settings()
class BlobObjectViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(BlobObjectViewTestCase, self).setUp()
        settings.GIT_STORAGE_ROOT = self.location
        self.storage = storage.GitStorage()
        self.view = views.TestBlobObjectView()
        self.view.storage = self.storage
        self.view.path = Path("foo/bar/baz/qux.txt")
        self.view.object = self.storage.repository.find_object(self.view.path)
        self.view.metadata = factories.BlobMetadataFactory(oid=self.view.object.hex, mimetype="text/plain")
        self.view.request = RequestFactory().request()
        self.view.request.path = self.view.path
        self.view.request.user = factories.SuperUserFactory()

    def test_object_type(self):
        self.assertIsNone(self.view.check_object_type())
        self.view.allowed_types = ()
        self.assertRaises(Http404, self.view.check_object_type)

    def test_check_permissions(self):
        self.assertRaises(NotImplementedError, self.view.check_permissions)

    def test_filter_directories(self):
        parent_path = self.view.path.parent_path
        tree = self.storage.repository.find_object(parent_path)
        directories = list(self.view.filter_directories(tree, parent_path))
        self.assertEqual(directories, [])

    def test_get_context_data(self):
        self.maxDiff = None
        context = self.view.get_context_data()
        context['root_directories'] = list(context['root_directories'])
        self.assertDictEqual(context, {
            'path': self.view.path,
            'object': self.view.object,
            'metadata': self.view.metadata,
            'root_directories': [
                {'name': "foo"},
                {'name': "path"}],
            'breadcrumbs': ["foo", "foo/bar", "foo/bar/baz", "foo/bar/baz/qux.txt"]})

    def test_dispatch(self):
        def check_permissions(self):
            self._permissions_checked = True
        self.view._permissions_checked = False
        self.view.check_permissions = types.MethodType(check_permissions, self.view)

        response = self.view.dispatch(self.view.request, self.view.path)
        self.assertContains(response, "foo/bar/baz/qux.txt")
        self.assertTrue(self.view._permissions_checked)
        self.assertIsNotNone(self.view.metadata)

    def test_dispatch_hidden(self):
        self.assertRaises(PermissionDenied, self.view.dispatch, self.view.request, "path/with/hidden/.file")

    def test_dispatch_unknown(self):
        self.assertRaises(Http404, self.view.dispatch, self.view.request, "toto/coin")


@override_settings()
class TreeObjectViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(TreeObjectViewTestCase, self).setUp()
        settings.GIT_STORAGE_ROOT = self.location
        self.storage = storage.GitStorage()
        self.view = views.TestTreeObjectView()
        self.view.storage = self.storage
        self.view.path = Path("path/with/hidden")
        self.view.object = self.storage.repository.find_object(self.view.path)
        self.view.request = RequestFactory().request()
        self.view.request.path = self.view.path
        self.view.request.user = factories.SuperUserFactory()

    def test_object_type(self):
        self.assertIsNone(self.view.check_object_type())
        self.view.allowed_types = ()
        self.assertRaises(Http404, self.view.check_object_type)

    def test_check_permissions(self):
        self.assertRaises(NotImplementedError, self.view.check_permissions)

    def test_filter_directories(self):
        directories = list(self.view.filter_directories(self.view.object, self.view.path))
        self.assertEqual(directories, [])

    def test_dispatch(self):
        def check_permissions(self):
            self._permissions_checked = True
        self.view._permissions_checked = False
        self.view.check_permissions = types.MethodType(check_permissions, self.view)

        response = self.view.dispatch(self.view.request, self.view.path)
        self.assertContains(response, "path/with/hidden")
        self.assertTrue(self.view._permissions_checked)
        self.assertEqual(self.view.metadata, models.TreeMetadata(oid=self.view.object.hex))

    def test_dispatch_hidden(self):
        self.assertRaises(PermissionDenied, self.view.dispatch, self.view.request, "path/with/hidden/.directory")

    def test_dispatch_unknown(self):
        self.assertRaises(Http404, self.view.dispatch, self.view.request, "toto/coin")


class BlobViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(BlobViewTestCase, self).setUp()
        self.storage = storage.GitStorage(self.location)
        self.view = views.TestBlobView()
        self.view.storage = self.storage
        self.view.path = Path("foo/bar/baz/qux.txt")
        self.view.object = self.storage.repository.find_object(self.view.path)
        self.view.metadata = factories.BlobMetadataFactory(oid=self.view.object.hex, mimetype="text/plain")
        self.view.request = RequestFactory().request()
        self.view.request.user = factories.UserFactory()

    def test_check_permissions(self):
        self.assertRaises(PermissionDenied, self.view.check_permissions)

    def test_delegate(self):
        parent_path = Path(self.view.path.parent_path)
        factories.TreePermissionFactory(parent_path=parent_path.parent_path, name=parent_path.name,
                                        user=self.view.request.user)
        self.assertIsNone(self.view.check_permissions())


class TreeViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(TreeViewTestCase, self).setUp()
        self.storage = storage.GitStorage(self.location)
        self.view = views.TestTreeView()
        self.view.storage = self.storage
        self.view.path = Path("foo/bar/baz")
        self.view.object = self.storage.repository.find_object(self.view.path)
        self.view.request = RequestFactory().request()
        self.view.request.user = factories.UserFactory()

    def test_check_permissions(self):
        self.assertRaises(PermissionDenied, self.view.check_permissions)

    def test_delegate(self):
        factories.TreePermissionFactory(parent_path=self.view.path.parent_path, name=self.view.path.name,
                                        user=self.view.request.user)
        self.assertIsNone(self.view.check_permissions())

    def test_filter_files(self):
        metadata = factories.BlobMetadataFactory(oid="100b0dec8c53a40e4de7714b2c612dad5fad9985", mimetype="text/plain")

        files = list(self.view.filter_files())
        self.assertEqual(files, [{'name': "qux.txt", 'metadata': metadata}])

    def test_filter_files_hidden(self):
        self.view = views.TestTreeView()
        self.view.storage = self.storage
        self.view.path = Path("path/with/hidden")
        self.view.object = self.storage.repository.find_object(self.view.path)
        self.view.request = RequestFactory().request()
        self.view.request.user = factories.UserFactory()
        files = list(self.view.filter_files())
        self.assertEqual(files, [])

    def test_get_context_data(self):
        metadata = factories.BlobMetadataFactory(oid="100b0dec8c53a40e4de7714b2c612dad5fad9985", mimetype="text/plain")

        self.maxDiff = None
        context = self.view.get_context_data()
        self.assertDictEqual(context, {
            'path': self.view.path,
            'object': self.view.object,
            'metadata': self.view.metadata,
            'root_directories': [],  # Access to nothing
            'breadcrumbs': ["foo", "foo/bar", "foo/bar/baz"],
            # Specific part
            'directories': [],
            'files': [{'name': "qux.txt", 'metadata': metadata}]})


class AdminPermissionTestCase(TestCase):

    def setUp(self):
        super(AdminPermissionTestCase, self).setUp()
        self.view = views.TestAdminView()
        self.view.request = RequestFactory().request()

    def test_check_permission(self):
        self.view.request.user = factories.UserFactory()
        self.assertRaises(PermissionDenied, self.view.check_permissions)
        self.view.request.user = factories.SuperUserFactory()
        self.assertRaises(views.StubValue, self.view.check_permissions)


@override_settings()
class RepositoryViewTestCase(VanillaRepositoryMixin, TestCase):

    def setUp(self):
        super(RepositoryViewTestCase, self).setUp()
        settings.GIT_STORAGE_ROOT = self.location
        self.view_class = views.TestRepositoryView
        self.view = self.view_class.as_view()
        self.request = RequestFactory().request()
        self.request.user = factories.SuperUserFactory()

    def test_initkwargs(self):
        self.assertRaises(TypeError, self.view_class.as_view, get=None)
        self.assertRaises(TypeError, self.view_class.as_view, foo=None)

    def test_blob_view(self):
        factories.BlobMetadataFactory(oid="100b0dec8c53a40e4de7714b2c612dad5fad9985", mimetype="text/plain")
        self.assertRaises(PermissionDenied, self.view, self.request, "foo/bar/baz/qux.txt/")
        self.view_class.type_to_view_class[pygit2.GIT_OBJ_BLOB] = views.TestBlobView
        response = self.view(self.request, "foo/bar/baz/qux.txt/")
        self.assertContains(response, "foo/bar/baz/qux.txt")

    def test_tree_view(self):
        self.assertRaises(PermissionDenied, self.view, self.request, "foo/bar/baz/")
        self.view_class.type_to_view_class[pygit2.GIT_OBJ_TREE] = views.TestTreeView
        response = self.view(self.request, "foo/bar/baz/")
        self.assertContains(response, "foo/bar/baz")

    def test_method_view(self):
        self.assertRaises(Http404, self.view, self.request, "foo/bar/baz/qux.txt/;download")

    def test_unknown_view(self):
        self.assertRaises(Http404, self.view, self.request, "toto")
