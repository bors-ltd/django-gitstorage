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

from functools import update_wrapper
import logging
import operator
from pathlib import Path
import unicodedata
import urllib.parse

from django.core.exceptions import PermissionDenied
from django.http.response import Http404, HttpResponse
from django.utils.decorators import classonlymethod
from django.views import generic as generic_views

import pygit2

from . import forms
from . import models
from . import repository


logger = logging.getLogger(__name__)


class ObjectViewMixin(object):
    """API common to all Git object views.

    You want to inherit from BlobViewMixin, TreeViewMixin, etc.
    """

    allowed_types = ()
    # Attributes available when rendering the view
    repo = None
    path = None
    git_obj = None
    object = None

    def check_object_type(self):
        """Some views only apply to blobs, other to trees."""
        logger.debug(
            "check_object_type git_obj=%s type=%s",
            self.git_obj.hex,
            self.git_obj.type_str,
        )
        if self.git_obj.type not in self.allowed_types:
            raise Http404()

    def check_permissions(self):
        """Abstract, no implicit permission."""
        raise NotImplementedError()

    def filter_trees(self, path: Path):
        """
        Filter tree entries of the given tree by permission allowance.

        Should be in TreeViewMixin buy we want the root trees on every page.
        """
        allowed_names = models.TreePermission.objects.allowed_names(
            self.request.user, path
        )
        filtered = []

        trees, _blobs = self.repo.listdir(path)
        for entry in trees:
            # Hide hidden files
            if entry.name[0] == ".":
                continue
            if allowed_names is not None and entry.name not in allowed_names:
                continue
            filtered.append(
                {
                    "name": entry.name,
                    "path": str(path / entry.name),
                    "tree": models.Tree(id=entry.hex),
                }
            )
        return sorted(filtered, key=operator.itemgetter("name"))

    def load_object(self):
        """Each Git object type has its own Django model.

        Trees are in-memory objects built on the fly.
        """
        if self.git_obj.type == pygit2.GIT_OBJ_BLOB:
            self.object = models.Blob(
                pk=self.git_obj.hex, name=self.path.name, size=self.git_obj.size
            )
        elif self.git_obj.type == pygit2.GIT_OBJ_TREE:
            self.object = models.Tree(pk=self.git_obj.hex)

    def get_context_data(self, **kwargs):
        """Context variables for any type of Git object and on every page."""
        context = super().get_context_data(**kwargs)

        root_trees = self.filter_trees(Path(""))

        breadcrumbs = []
        path = self.path
        while path != Path("."):
            breadcrumbs.insert(0, path)
            path = path.parent

        context["path"] = self.path
        context["git_obj"] = self.git_obj
        context["object"] = self.object
        context["root_trees"] = root_trees
        context["breadcrumbs"] = breadcrumbs
        return context

    def dispatch(self, request, path, repo=None, git_obj=None, *args, **kwargs):
        """Filtering of hidden files and setting the instance attributes before dispatching."""
        logger.debug(
            "dispatch self=%s path=%s git_obj=%s args=%s kwargs=%s",
            self,
            path,
            git_obj,
            args,
            kwargs,
        )
        path = Path(path)
        self.path = path

        name = path.name
        if name and name[0] == ".":
            raise PermissionDenied()

        if not repo:
            repo = repository.Repository()
        self.repo = repo

        if not git_obj:
            try:
                git_obj = self.repo.open(path)
            except KeyError:
                raise Http404()

        self.git_obj = git_obj
        self.check_object_type()
        self.load_object()

        logger.debug("calling check_permissions %s", self.check_permissions)
        self.check_permissions()

        return super().dispatch(request, path, *args, **kwargs)


class BlobViewMixin(ObjectViewMixin):
    """View that applies only to blobs (files).

    Permission is checked on the parent tree.
    """

    allowed_types = (pygit2.GIT_OBJ_BLOB,)

    def check_permissions(self):
        if not models.TreePermission.objects.is_allowed(
            self.request.user, self.path.parent
        ):
            raise PermissionDenied()


class DownloadViewMixin(BlobViewMixin):
    """Download blob data from the storage once permissions are cleared."""

    attachment = True

    def get(self, request, *args, **kwargs):
        disposition = ["attachment" if self.attachment else "inline"]

        # Clean up filesystem idiosyncrasies: "de\u0301po\u0302t.jpg" -> "dépôt.jpg"
        attachment_filename = unicodedata.normalize("NFKC", self.path.name)
        ascii_filename = unicodedata.normalize("NFKD", attachment_filename)
        ascii_filename = ascii_filename.encode("ascii", "ignore").decode()
        disposition.append(f'filename="{ascii_filename}"')

        if ascii_filename != attachment_filename:
            quoted_filename = urllib.parse.quote(attachment_filename)
            disposition.append(f"filename*=UTF-8''{quoted_filename}")

        # The context manager will "release" the buffer on exit
        with memoryview(self.git_obj) as m:
            response = HttpResponse(m)
            response["Content-Type"] = self.object.mimetype
            if self.object.encoding:
                response["Content-Encoding"] = self.object.encoding
            response["Content-Disposition"] = "; ".join(disposition)
            # Content-Length comes from the memory object length

            return response


class InlineViewMixin(DownloadViewMixin):
    """Same as download but try and display the file within the browser."""

    attachment = False


class TreeViewMixin(ObjectViewMixin):
    """View that applies only to trees.

    Permission is checked on the path itself.
    """

    allowed_types = (pygit2.GIT_OBJ_TREE,)
    sort_key = operator.itemgetter("name")
    sort_reverse = False

    def check_permissions(self):
        if not models.TreePermission.objects.is_allowed(self.request.user, self.path):
            raise PermissionDenied()

    def filter_blobs(self):
        _trees, blobs = self.repo.listdir(self.path)

        objects = []
        for entry in blobs:
            # Hide hidden files
            if entry.name[0] == ".":
                continue
            # No check on allowed_names, all blobs are readable if their parent tree is
            objects.append(
                {
                    "name": entry.name,
                    "path": str(self.path / entry.name),
                    "blob": models.Blob(pk=entry.hex, name=entry.name),  # No size!
                }
            )

        return sorted(objects, key=self.sort_key, reverse=self.sort_reverse)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["trees"] = self.filter_trees(self.path)
        context["blobs"] = self.filter_blobs()
        return context


class SharesViewMixin(TreeViewMixin):
    form_class = forms.RemoveUsersForm

    def get_form(self):
        current_permissions = models.TreePermission.objects.current_permissions(
            self.path
        )
        current_user_ids = current_permissions.values_list("user", flat=True)

        return self.get_form_class()(current_user_ids, **self.get_form_kwargs())

    def form_valid(self, form):
        users = form.cleaned_data["users"]
        models.TreePermission.objects.remove(users, self.path)

        return super().form_valid(form)


class ShareViewMixin(TreeViewMixin):
    form_class = forms.AddUsersForm

    def get_form(self):
        current_permissions = models.TreePermission.objects.current_permissions(
            self.path
        )
        current_user_ids = current_permissions.values_list("user", flat=True)

        return self.get_form_class()(current_user_ids, **self.get_form_kwargs())

    def form_valid(self, form):
        users = form.cleaned_data["users"]
        models.TreePermission.objects.add(users, self.path)

        return super().form_valid(form)


class AdminPermissionMixin(object):
    """Enforce permission to require superuser, whatever the Git object type."""

    def check_permissions(self):
        if not self.request.user.is_superuser:
            raise PermissionDenied()
        # This is the only condition, permissions don't make sense once you're admin


class AuthenticatedPermissionMixin(object):
    def check_permissions(self):
        if not self.request.user.is_authenticated:
            raise PermissionDenied()
        # Being authenticated is good but not enough
        return super().check_permissions()


class BaseRepositoryView(ObjectViewMixin, generic_views.View):
    """Map URL path to the Git object at the same path, then return the dedicated view.

    This view is useless without a configured "type_to_view_class".
    """

    type_to_view_class = {
        # pygit2.GIT_OBJ_TREE: MyTreeView,
        # pygit2.GIT_OBJ_BLOB: MyBlobView,
    }

    @classonlymethod
    def as_view(cls, **initkwargs):
        """
        Main entry point for a request-response process.

        Borrowed from django.views.generic.View.
        """
        # sanitize keyword arguments
        for key in initkwargs:
            if key in cls.http_method_names:
                raise TypeError(
                    "You tried to pass in the %s method name as a "
                    "keyword argument to %s(). Don't do that." % (key, cls.__name__)
                )
            if not hasattr(cls, key):
                raise TypeError(
                    "%s() received an invalid keyword %r. as_view "
                    "only accepts arguments that are already "
                    "attributes of the class." % (cls.__name__, key)
                )

        def view(request, path, *args, **kwargs):
            # BEGIN gitstorage specific
            repo = kwargs["repo"] = repository.Repository()

            # Path methods must be mapped in the URLconf
            path = Path(path)
            if path.name and path.name[0] == ";":
                raise Http404()

            try:
                git_obj = kwargs["git_obj"] = repo.open(path)
            except KeyError:
                raise Http404()

            # Find a view class dedicated to this object's type
            try:
                view_class = cls.type_to_view_class[git_obj.type]
            except KeyError:
                raise PermissionDenied()
            # END gitstorage specific

            self = view_class(**initkwargs)
            if hasattr(self, "get") and not hasattr(self, "head"):
                self.head = self.get
            self.setup(request, *args, **kwargs)
            if not hasattr(self, "request"):
                raise AttributeError(
                    "%s instance has no 'request' attribute. Did you override "
                    "setup() and forget to call super()?" % cls.__name__
                )
            return self.dispatch(request, path, *args, **kwargs)

        view.view_class = cls
        view.view_initkwargs = initkwargs

        # take name and docstring from class
        update_wrapper(view, cls, updated=())

        # and possible attributes set by decorators
        # like csrf_exempt from dispatch
        update_wrapper(view, cls.dispatch, assigned=())
        return view
