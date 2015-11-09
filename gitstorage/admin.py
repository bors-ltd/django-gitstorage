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

from django.contrib import admin

from . import models


class BlobMetadataAdmin(admin.ModelAdmin):
    search_fields = ['id', 'mimetype']
    list_filter = ['mimetype']

admin.site.register(models.BlobMetadata, BlobMetadataAdmin)


class TreePermissionAdmin(admin.ModelAdmin):
    search_fields = ['parent_path', 'name']
    list_filter = ['user']

admin.site.register(models.TreePermission, TreePermissionAdmin)
