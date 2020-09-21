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

from django.db import models
from django.utils.translation import gettext_lazy as _

from . import mimetypes
from . import validators
from .conf import settings


class BaseObject(models.Model):
    id = models.CharField(
        primary_key=True,
        editable=False,
        max_length=40,  # I prefer the hexadecimal version
    )

    class Meta:
        abstract = True


class Blob(BaseObject):
    name = models.CharField(max_length=200)
    size = models.IntegerField()

    _mimetype = None
    _encoding = None

    class Meta:
        managed = False  # Built in-memory on the fly

    def __str__(self):
        return self.id

    def guess_type(self):
        mimetype, encoding = mimetypes.guess_type(self.name)
        return mimetype or "application/octet-stream", encoding

    @property
    def mimetype(self):
        if not self._mimetype:
            self._mimetype, self._encoding = self.guess_type()
        return self._mimetype

    @property
    def encoding(self):
        if not self._mimetype:  # Don't use optional encoding
            self._mimetype, self._encoding = self.guess_type()
        return self._encoding


class Tree(BaseObject):
    class Meta:
        managed = False  # Built in-memory on the fly

    def __str__(self):
        return self.id


class TreePermissionQuerySet(models.QuerySet):
    def current_permissions(self, path: Path, **kwargs):
        return self.filter(
            parent_path=path.parent, name=path.name, **kwargs
        ).select_related("user")

    def allowed_names(self, user, parent_path: Path, **kwargs):
        if user:
            if user.is_superuser:
                # Reads as no restriction
                return None
            if not user.is_authenticated:
                user = None
        return self.filter(parent_path=parent_path, user=user, **kwargs).values_list(
            "name", flat=True
        )

    def allowed_paths(self, user):
        if user:
            if user.is_superuser:
                # Reads as no restriction
                return None
            if not user.is_authenticated:
                user = None
        all_permissions = self.filter(user=user).values_list("parent_path", "name")
        return ["/".join(filter(None, segments)) for segments in all_permissions]

    def for_user(self, user, path: Path, **kwargs):
        if user and not user.is_authenticated:
            user = None
        qs = self.filter(user=user, parent_path=path.parent, name=path.name, **kwargs)
        return qs

    def other_permissions(self, user, path: Path, **kwargs):
        if user and not user.is_authenticated:
            user = None
        return (
            self.filter(user=user, parent_path=path.parent, **kwargs)
            .exclude(name=path.name)
            .exists()
        )

    def is_allowed(self, user, path: Path, **kwargs):
        if user and user.is_superuser:
            return True
        return self.for_user(user, path, **kwargs).exists()

    def add(self, users, path: Path):
        for user in users:
            self.get_or_create(parent_path=path.parent, name=path.name, user=user)

    def remove(self, users, path: Path):
        # Does not work for [None]
        if users == [None]:
            self.filter(parent_path=path.parent, name=path.name, user=None).delete()
        else:
            self.filter(
                parent_path=path.parent, name=path.name, user__in=users
            ).delete()


class TreePermission(models.Model):
    parent_path = models.CharField(
        _("parent path"),
        max_length=2048,
        db_index=True,
        blank=True,
        validators=[validators.path_validator],
    )
    name = models.CharField(
        _("name"),
        max_length=256,
        db_index=True,
        blank=True,
        validators=[validators.name_validator],
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,  # For anonymous user
        blank=True,
        on_delete=models.CASCADE,
    )

    objects = TreePermissionQuerySet.as_manager()

    class Meta:
        verbose_name = _("tree permission")
        verbose_name_plural = _("tree permissions")

    def __str__(self):
        path = Path(self.parent_path) / self.name
        return "{0} on {1}".format(self.user, path)
