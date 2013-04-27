# -*- coding: utf-8 -*-
# Copyright 2013 Bors Ltd
# This file is part of django-gitstorage.
#
#    django-gitstorage is free software: you can redistribute it and/or modify
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

from django.contrib.auth import models as auth_models
from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import mimetypes
from . import utils
from . import validators


class BaseObjectMetadata(models.Model):
    oid = models.CharField(_("oid"), primary_key=True, unique=True, db_index=True, editable=False, max_length=40)
    mimetype = models.CharField(_("mimetype"), max_length=255, null=True, blank=True)

    class Meta:
        abstract = True


class TreeMetadata(BaseObjectMetadata):

    class Meta:
        managed = False

    def __unicode__(self):
        return "{0.oid}".format(self)


class BlobMetadataManager(models.Manager):

    def create_from_name(self, name, oid, **kwargs):
        mimetype = mimetypes.guess_type(name)[0]
        return self.create(oid=oid, mimetype=mimetype, **kwargs)

    def create_from_content(self):
        # Could "file -i" the blob content
        raise NotImplementedError()


class BlobMetadata(BaseObjectMetadata):

    objects = BlobMetadataManager()

    class Meta:
        verbose_name = _("blob metadata")
        verbose_name_plural = _("blob metadata")

    def __unicode__(self):
        return "{0.oid} type={0.mimetype}".format(self)


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

    def __unicode__(self):
        path = utils.Path(self.parent_path)
        path = path.resolve(self.name)
        return "{0} on {1}".format(self.user, path)
