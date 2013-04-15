# -*- coding: utf-8 -*-
# Copyright 2013 Bors Ltd
#This file is part of GitStorage.
#
#    GitStorage is free software: you can redistribute it and/or modify
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

from django.core.management.base import NoArgsCommand

from gitstorage import models
from gitstorage import wrappers
from gitstorage import storage as git_storage


class Command(NoArgsCommand):
    help = "Compute metadata for new blobs"

    def sync_tree(self, tree):
        for entry in tree:
            if entry.attributes == wrappers.GIT_FILEMODE_TREE:
                self.sync_tree(entry.to_object())
            elif entry.attributes in wrappers.GIT_FILEMODE_BLOB_KINDS:
                if entry.hex in self.known_blobs:
                    continue
                models.BlobMetadata.objects.create_from_name(entry.name, entry.hex)
                self.known_blobs.add(entry.hex)

    def handle_noargs(self, **options):
        storage = git_storage.GitStorage()
        repository = storage.repository

        self.known_blobs = set(models.BlobMetadata.objects.values_list('oid', flat=True))

        self.sync_tree(repository.head.tree)
