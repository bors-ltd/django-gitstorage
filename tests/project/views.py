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

from django.http.response import HttpResponse
from django.views import generic

from gitstorage import views


class TestFormViewMixin(object):
    success_url = "/success/"

    def form_invalid(self, form):
        return HttpResponse(str(form.errors))


class TestPreviewView(views.PreviewViewMixin, generic.TemplateView):
    template_name = "base.html"


class TestDownloadView(views.DownloadViewMixin, generic.TemplateView):
    template_name = "base.html"


class TestSharesView(views.SharesViewMixin, TestFormViewMixin, generic.FormView):
    template_name = "base.html"

    def get(self, request, *args, **kwargs):
        return HttpResponse("shares", *args, **kwargs)


class TestShareView(views.ShareViewMixin, TestFormViewMixin, generic.FormView):
    template_name = "base.html"

    def get(self, request, *args, **kwargs):
        return HttpResponse("share", *args, **kwargs)


class TestBlobView(views.BlobViewMixin, generic.TemplateView):
    template_name = "base.html"


class TestTreeView(views.TreeViewMixin, generic.TemplateView):
    template_name = "base.html"


class TestRepositoryView(views.BaseRepositoryView):
    type_to_view_class = {
        pygit2.GIT_OBJ_BLOB: TestBlobView,
        pygit2.GIT_OBJ_TREE: TestTreeView,
    }


class DummyRepositoryView(views.BaseRepositoryView):
    # Don't implement type_to_view_class
    pass


class DummyAdminShareView(views.AdminPermissionMixin, views.ShareViewMixin, generic.View):
    pass


class DummyTreeView(views.TreeViewMixin, generic.View):
    pass


class DummyBlobView(views.BlobViewMixin, generic.View):
    pass
