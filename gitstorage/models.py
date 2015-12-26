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

import magic

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib.auth import models as auth_models
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import mimetypes
from . import utils
from . import validators


def get_blob_metadata_model():
    """
    Returns the BlobMetadata model that is active in this project.
    """
    try:
        return django_apps.get_model(settings.GIT_STORAGE_BLOB_METADATA_MODEL)
    except ValueError:
        raise ImproperlyConfigured("GIT_STORAGE_BLOB_METADATA_MODEL must be of the form 'app_label.model_name'")
    except LookupError:
        raise ImproperlyConfigured(
            "GIT_STORAGE_BLOB_METADATA_MODEL refers to model '%s' that has not been installed" % (
                settings.GIT_STORAGE_BLOB_METADATA_MODEL,
            )
        )
    except AttributeError:
        return BlobMetadata


def guess_mimetype(name=None, buffer=None):
    mimetype = None
    if name is not None:
        mimetype = mimetypes.guess_type(name)[0]
    # Mimetype guessing on name is not more accurate but more easily extensible
    if mimetype is None and buffer is not None:
        mimetype = magic.from_buffer(buffer, mime=True).decode()
    return mimetype


class BaseObjectMetadata(models.Model):
    id = models.CharField(_("id"), primary_key=True, unique=True, db_index=True, editable=False, max_length=40)
    mimetype = models.CharField(_("mimetype"), max_length=255, null=True, blank=True)

    def fill(self, repository, name, blob, **kwargs):
        if self.mimetype is None:
            self.mimetype = guess_mimetype(name=name, buffer=blob.data)

    class Meta:
        abstract = True


class TreeMetadata(BaseObjectMetadata):

    class Meta:
        managed = False

    def __str__(self):
        return "{0.id}".format(self)


class BlobMetadata(BaseObjectMetadata):

    class Meta:
        verbose_name = _("blob metadata")
        verbose_name_plural = _("blob metadata")
        swappable = 'GIT_STORAGE_BLOB_METADATA_MODEL'

    def __str__(self):
        return "{0.id} type={0.mimetype}".format(self)


class TreePermissionManager(models.Manager):

    def current_permissions(self, path, **kwargs):
        return self.filter(parent_path=path.parent_path, name=path.name, **kwargs).select_related('user')

    def allowed_names(self, user, parent_path, **kwargs):
        if user:
            if user.is_superuser:
                # Reads as no restriction
                return None
            if not user.is_authenticated():
                user = None
        return self.filter(parent_path=parent_path, user=user, **kwargs).values_list('name', flat=True)

    def allowed_paths(self, user):
        if user:
            if user.is_superuser:
                # Reads as no restriction
                return None
            if not user.is_authenticated():
                user = None
        all_permissions = self.filter(user=user).values_list('parent_path', 'name')
        return [parent_path + "/" + name for parent_path, name in all_permissions]

    def for_user(self, user, path, **kwargs):
        if user:
            if not user.is_authenticated():
                user = None
        return self.filter(user=user, parent_path=path.parent_path, name=path.name, **kwargs)

    def other_permissions(self, user, path, **kwargs):
        if user:
            if not user.is_authenticated():
                user = None
        return self.filter(user=user, parent_path=path.parent_path, **kwargs).exclude(name=path.name).exists()

    def is_allowed(self, user, path, **kwargs):
        if user:
            if user.is_superuser:
                return True
        return self.for_user(user, path, **kwargs).exists()

    def add(self, users, path):
        for user in users:
            self.get_or_create(parent_path=path.parent_path, name=path.name, user=user)

    def remove(self, users, path):
        # Does not work for [None]
        if None in users:
            for user in users:
                self.filter(parent_path=path.parent_path, name=path.name, user=user).delete()
        else:
            self.filter(parent_path=path.parent_path, name=path.name, user__in=users).delete()


class TreePermission(models.Model):
    parent_path = models.CharField(_("parent path"), max_length=2048, db_index=True, blank=True,
                                   validators=[validators.path_validator])
    name = models.CharField(_("name"), max_length=256, db_index=True, blank=True,
                            validators=[validators.name_validator])
    user = models.ForeignKey(auth_models.User, null=True, blank=True)  # For anonymous user

    objects = TreePermissionManager()

    class Meta:
        verbose_name = _("tree permission")
        verbose_name_plural = _("tree permissions")

    def __str__(self):
        path = utils.Path(self.parent_path).resolve(self.name)
        return "{0} on {1}".format(self.user, path)
