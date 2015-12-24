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

from django.contrib.auth import models as auth_models
from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import mimetypes
from . import utils
from . import validators


class BaseObjectMetadata(models.Model):
    id = models.CharField(_("id"), primary_key=True, unique=True, db_index=True, editable=False, max_length=40)
    mimetype = models.CharField(_("mimetype"), max_length=255, null=True, blank=True)

    class Meta:
        abstract = True


class TreeMetadata(BaseObjectMetadata):

    class Meta:
        managed = False

    def __str__(self):
        return "{0.id}".format(self)


class BlobMetadataManager(models.Manager):

    def create_from_name(self, name, id, **kwargs):
        mimetype = mimetypes.guess_type(name)[0]
        return self.create(id=id, mimetype=mimetype, **kwargs)

    def create_from_content(self, repository, id, **kwargs):
        blob = repository[id]
        mimetype = magic.from_buffer(blob.data, mime=True).decode()
        return self.create(id=id, mimetype=mimetype, **kwargs)


class BlobMetadata(BaseObjectMetadata):

    objects = BlobMetadataManager()

    class Meta:
        verbose_name = _("blob metadata")
        verbose_name_plural = _("blob metadata")

    def __str__(self):
        return "{0.id} type={0.mimetype}".format(self)


class TreePermissionManager(models.Manager):

    def current_permissions(self, path, **kwargs):
        return self.filter(parent_path=path.parent_path, name=path.name, **kwargs).select_related('user')

    def allowed_names(self, user, parent_path, **kwargs):
        if user.is_anonymous():
            # Reads as none allowed
            return []
        elif user.is_superuser:
            # Reads as not applicable
            return None
        return self.filter(parent_path=parent_path, user=user, **kwargs).values_list('name', flat=True)

    def is_allowed(self, user, path, **kwargs):
        if user.is_anonymous():
            return False
        elif user.is_superuser:
            return True
        return self.filter(parent_path=path.parent_path, name=path.name, user=user, **kwargs).exists()

    def add(self, users, path):
        for user in users:
            self.get_or_create(parent_path=path.parent_path, name=path.name, user=user)

    def remove(self, users, path):
        self.filter(parent_path=path.parent_path, name=path.name, user__in=users).delete()


class TreePermission(models.Model):
    parent_path = models.CharField(_("parent path"), max_length=2048, db_index=True, blank=True,
                                   validators=[validators.path_validator])
    name = models.CharField(_("name"), max_length=256, db_index=True, blank=True,
                            validators=[validators.name_validator])
    user = models.ForeignKey(auth_models.User)

    objects = TreePermissionManager()

    class Meta:
        verbose_name = _("tree permission")
        verbose_name_plural = _("tree permissions")

    def __str__(self):
        path = utils.Path(self.parent_path).resolve(self.name)
        return "{0} on {1}".format(self.user, path)
