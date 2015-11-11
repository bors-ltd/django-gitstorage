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

from django.http.response import HttpResponse
from django.views import generic

import pygit2

from gitstorage import views


class TestViewMixin(object):

    def get_context_data(self, **kwargs):
        return kwargs


class TestFormViewMixin(TestViewMixin):

    def get_success_url(self):
        return "/success/"

    def form_invalid(self, form):
        return HttpResponse("invalid")


class TestPreviewView(views.PreviewViewMixin, TestViewMixin, generic.View):
    pass


class TestDownloadView(views.DownloadViewMixin, TestViewMixin, generic.View):
    pass


class TestDeleteView(views.DeleteViewMixin, TestViewMixin, generic.View):
    pass


class TestUploadView(views.UploadViewMixin, TestFormViewMixin, generic.FormView):
    pass


class TestSharesView(views.SharesViewMixin, TestFormViewMixin, generic.FormView):

    def get(self, request, *args, **kwargs):
        return HttpResponse("shares", *args, **kwargs)


class TestShareView(views.ShareViewMixin, TestFormViewMixin, generic.FormView):

    def get(self, request, *args, **kwargs):
        return HttpResponse("share", *args, **kwargs)


class TestBlobObjectView(views.ObjectViewMixin, TestViewMixin, generic.View):
    allowed_types = (pygit2.GIT_OBJ_BLOB,)

    def get(self, request, *args, **kwargs):
        return HttpResponse(self.path, *args, **kwargs)


class TestTreeObjectView(views.ObjectViewMixin, TestViewMixin, generic.View):
    allowed_types = (pygit2.GIT_OBJ_TREE,)

    def get(self, request, *args, **kwargs):
        return HttpResponse(self.path, *args, **kwargs)


class TestBlobView(views.BlobViewMixin, generic.View):

    def get(self, request, *args, **kwargs):
        return HttpResponse(self.path, *args, **kwargs)


class TestTreeView(views.TreeViewMixin, TestViewMixin, generic.View):

    def get(self, request, *args, **kwargs):
        return HttpResponse(self.path, *args, **kwargs)


class StubValue(Exception):
    pass


class StubPermissionMixin(object):

    def check_permissions(self):
        raise StubValue()


class TestAdminView(views.AdminPermissionMixin, StubPermissionMixin, generic.View):
    pass


class TestBaseRepositoryView(views.BaseRepositoryView):
    pass
