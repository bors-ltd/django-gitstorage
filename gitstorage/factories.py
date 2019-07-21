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
import factory

from django.contrib.auth import models as auth_models

from gitstorage import models


class AnonymousUserFactory(factory.Factory):
    class Meta:
        model = auth_models.AnonymousUser


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = auth_models.User

    username = factory.Sequence("john{}".format)
    first_name = factory.Sequence("John{}".format)
    last_name = factory.Sequence("Doe{}".format)
    email = factory.Sequence("john.doe{}@example.com".format)

    @classmethod
    def _prepare(cls, create, **kwargs):
        password = kwargs.pop("password", None)
        user = super()._prepare(create, **kwargs)
        if password:
            user.set_password(password)
            if create:
                user.save()
        return user


class SuperUserFactory(UserFactory):
    username = factory.Sequence("admin{0}".format)
    is_superuser = True


class BlobFactory(factory.DjangoModelFactory):
    size = 0

    class Meta:
        model = models.Blob


class TreeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Tree

    @classmethod
    def _generate_next_sequence(cls):
        """managed = False"""
        return None


class TreePermissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.TreePermission

    parent_path = factory.Sequence("parent{0}".format)
    name = factory.Sequence("name{0}".format)
    user = factory.SubFactory(UserFactory)
