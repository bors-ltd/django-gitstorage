# This file is part of django-gitstorage.
#
#    Django-gitstorage is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
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

from pathlib import Path

import pygit2

from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone
from django.http.response import Http404
from django.test import TestCase
from django.test.client import RequestFactory

from gitstorage import factories
from gitstorage import models
from gitstorage import repository
from gitstorage.tests.utils import VanillaRepositoryMixin

from tests.project import views


class BaseViewTestCase(VanillaRepositoryMixin, TestCase):
    path = None

    def setUp(self):
        super().setUp()
        self.repo = repository.Repository()

        if self.path is None:
            raise ValueError("Forgot to declare a path!")

        self.path = Path(self.path)
        self.user = factories.UserFactory(password="password")
        assert self.client.login(username=self.user.username, password="password")

        git_obj = self.repo.open(self.path)

        if git_obj.type == pygit2.GIT_OBJ_BLOB:
            self.git_obj = git_obj

            # Permission to parent path
            parent = self.path.parent
            self.permission = factories.TreePermissionFactory(
                parent_path=parent.parent, name=parent.name, user=self.user
            )

            # Blob object
            self.blob = factories.BlobFactory(
                id=self.git_obj.hex,
                size=self.git_obj.size,
                data=SimpleUploadedFile(self.path.name, self.git_obj.data),
            )

        elif git_obj.type == pygit2.GIT_OBJ_TREE:
            self.git_obj = git_obj

            # Permission to itself
            factories.TreePermissionFactory(
                parent_path=self.path.parent, name=self.path.name, user=self.user
            )


class DownloadViewTestCase(BaseViewTestCase):
    path = "path/with/unicode/de\u0301po\u0302t.txt"

    def test_get(self):
        response = self.client.get(reverse("blob_download", args=[self.path]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Disposition"],
            "attachment; filename=\"depot.txt\"; filename*=UTF-8''d%C3%A9p%C3%B4t.txt",
        )


class InlineViewTestCase(BaseViewTestCase):
    path = "path/with/unicode/de\u0301po\u0302t.txt"

    def test_get(self):
        response = self.client.get(reverse("blob_inline", args=[self.path]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Length"], "9")


class SharesViewTestCase(BaseViewTestCase):
    path = "foo/bar/baz"

    def test_get(self):
        response = self.client.get(reverse("tree_shares", args=[self.path]))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        user = factories.UserFactory()
        factories.TreePermissionFactory(
            parent_path=self.path.parent, name=self.path.name, user=user
        )

        response = self.client.post(reverse("tree_shares", args=[self.path]))
        self.assertEqual(response.status_code, 200)

        data = {"users": user.pk}
        response = self.client.post(reverse("tree_shares", args=[self.path]), data=data)
        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            models.TreePermission.objects.filter(
                parent_path="foo/bar", name="baz", user=user
            ).exists()
        )

        # Re-remove the same
        response = self.client.post(reverse("tree_shares", args=[self.path]), data=data)
        self.assertEqual(response.status_code, 200)


class ShareViewTestCase(BaseViewTestCase):
    path = "foo/bar/baz"

    def test_get(self):
        response = self.client.get(reverse("tree_share", args=[self.path]))
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        user = factories.UserFactory()

        response = self.client.post(reverse("tree_share", args=[self.path]))
        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            models.TreePermission.objects.filter(
                parent_path="foo/bar", name="baz", user=user
            ).exists()
        )

        data = {"users": user.pk}
        response = self.client.post(reverse("tree_share", args=[self.path]), data=data)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            models.TreePermission.objects.filter(
                parent_path="foo/bar", name="baz", user=user
            ).exists()
        )

        # Re-add the same
        response = self.client.post(reverse("tree_share", args=[self.path]), data=data)
        self.assertEqual(response.status_code, 200)


class BlobViewTestCase(BaseViewTestCase):
    path = "foo/bar/baz/qux.txt"

    def test_object_type(self):
        view = views.TestBlobView(git_obj=self.git_obj)
        self.assertIsNone(view.check_object_type())
        view.allowed_types = ()
        self.assertRaises(Http404, view.check_object_type)

    def test_get_context_data(self):
        self.maxDiff = None

        response = self.client.get(reverse("repo_browse", args=[self.path]))
        context = response.context
        self.assertEqual(context["path"], self.path)
        self.assertEqual(context["git_obj"].id, self.git_obj.id)
        self.assertEqual(context["object"].id, self.blob.id)
        self.assertEqual(list(context["root_trees"]), [])  # No permission on root
        self.assertEqual(
            context["breadcrumbs"],
            ["foo", "foo/bar", "foo/bar/baz", "foo/bar/baz/qux.txt"],
        )

    def test_get_hidden(self):
        response = self.client.get(
            reverse("repo_browse", args=["path/with/hidden/.file"])
        )
        self.assertEqual(response.status_code, 403)

    def test_get_unknown(self):
        response = self.client.get(reverse("repo_browse", args=["toto/coin"]))
        self.assertEqual(response.status_code, 404)

    def test_check_permissions(self):
        response = self.client.get(reverse("repo_browse", args=[self.path]))
        self.assertEqual(response.status_code, 200)

        user = factories.UserFactory(password="password")
        assert self.client.login(username=user.username, password="password")
        response = self.client.get(reverse("repo_browse", args=[self.path]))
        self.assertEqual(response.status_code, 403)

        tree_path = self.path.parent
        factories.TreePermissionFactory(
            parent_path=tree_path.parent, name=tree_path.name, user=user
        )
        response = self.client.get(reverse("repo_browse", args=[self.path]))
        self.assertEqual(response.status_code, 200)


class TreeViewTestCase(BaseViewTestCase):
    path = "foo/bar/baz"

    def setUp(self):
        super().setUp()
        # A blob found in the path
        git_obj = self.repo.open("foo/bar/baz/qux.txt")
        self.blob = factories.BlobFactory(id=git_obj.hex)

    def test_object_type(self):
        view = views.TestTreeView(git_obj=self.git_obj)
        self.assertIsNone(view.check_object_type())
        view.allowed_types = ()
        self.assertRaises(Http404, view.check_object_type)

    def test_get_context_data(self):
        self.maxDiff = None

        response = self.client.get(reverse("repo_browse", args=[self.path]))
        context = response.context
        self.assertEqual(response.status_code, 200)
        self.assertEqual(context["path"], self.path)
        self.assertEqual(context["git_obj"].hex, self.git_obj.hex)
        self.assertEqual(context["object"].id, self.git_obj.hex)
        self.assertEqual(context["root_trees"], [])  # No permission on root
        self.assertEqual(context["breadcrumbs"], ["foo", "foo/bar", "foo/bar/baz"])
        self.assertEqual(context["trees"], [])
        self.assertEqual(len(context["blobs"]), 1)
        blob = context["blobs"][0]
        self.assertEqual(blob["name"], "qux.txt")
        self.assertEqual(blob["path"], "foo/bar/baz/qux.txt")
        self.assertEqual(blob["blob"], self.blob)
        self.assertAlmostEqual(
            blob["ctime"].timestamp(), timezone.now().timestamp(), delta=1
        )
        self.assertAlmostEqual(
            blob["mtime"].timestamp(), timezone.now().timestamp(), delta=1
        )

    def test_get_hidden(self):
        response = self.client.get(
            reverse("repo_browse", args=["path/with/hidden/.directory"])
        )
        self.assertEqual(response.status_code, 403)

    def test_get_unknown(self):
        response = self.client.get(reverse("repo_browse", args=["toto/coin"]))
        self.assertEqual(response.status_code, 404)

    def test_check_permissions(self):
        response = self.client.get(reverse("repo_browse", args=[self.path]))
        self.assertEqual(response.status_code, 200)

        user = factories.UserFactory(password="password")
        assert self.client.login(username=user.username, password="password")
        response = self.client.get(reverse("repo_browse", args=[self.path]))
        self.assertEqual(response.status_code, 403)

        factories.TreePermissionFactory(
            parent_path=self.path.parent, name=self.path.name, user=user
        )
        response = self.client.get(reverse("repo_browse", args=[self.path]))
        self.assertEqual(response.status_code, 200)


class AdminPermissionTestCase(BaseViewTestCase):
    path = ""

    def setUp(self):
        super().setUp()
        # A blob found at the root
        self.git_obj = self.repo.open("foo.txt")
        self.blob = factories.BlobFactory(id=self.git_obj.hex)

    def test_check_permission(self):
        user = factories.UserFactory(password="pass1")
        assert self.client.login(username=user.username, password="pass1")
        response = self.client.get(reverse("repo_browse", args=[""]))
        self.assertEqual(response.status_code, 403)

        superuser = factories.SuperUserFactory(password="pass2")
        assert self.client.login(username=superuser.username, password="pass2")
        response = self.client.get(reverse("repo_browse", args=[""]))
        self.assertEqual(response.status_code, 200)


class CoverageTestCase(VanillaRepositoryMixin, TestCase):
    """Edge cases to reach 100 % coverage."""

    def setUp(self):
        super().setUp()
        self.repo = repository.Repository()

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
        view = views.DummyAdminShareView(request=request, path=Path(""))
        self.assertRaises(PermissionDenied, view.check_permissions)

        request = RequestFactory()
        request.user = factories.SuperUserFactory()
        view = views.DummyAdminShareView(request=request, path=Path(""))
        self.assertIsNone(view.check_permissions())

    def test_filter_hidden(self):
        request = RequestFactory()
        request.user = factories.UserFactory()
        view = views.DummyTreeView(
            request=request, path=Path("path/with/hidden"), repo=self.repo
        )

        blobs = view.filter_blobs()
        self.assertNotIn(".file", [entry["name"] for entry in blobs])

        trees = view.filter_trees(view.path)
        self.assertNotIn(".directory", [entry["name"] for entry in trees])

    def test_dispatch_not_found(self):
        request = RequestFactory()
        request.user = factories.UserFactory()
        view = views.DummyTreeView()
        self.assertRaises(Http404, view.dispatch, request, path=Path("tot/coin"))
