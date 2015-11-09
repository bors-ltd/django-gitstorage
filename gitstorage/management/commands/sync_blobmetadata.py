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

from django.core.management.base import NoArgsCommand

from gitstorage import models
from gitstorage import wrappers
from gitstorage import storage as git_storage


class Command(NoArgsCommand):
    help = "Compute metadata for new blobs"

    def sync_tree(self, tree):
        for entry in tree:
            if entry.filemode == wrappers.GIT_FILEMODE_TREE:
                self.sync_tree(self.repository[entry.id])
            elif entry.filemode in wrappers.GIT_FILEMODE_BLOB_KINDS:
                if entry.hex in self.known_blobs:
                    continue
                models.BlobMetadata.objects.create_from_name(entry.name, entry.hex)
                self.known_blobs.add(entry.hex)

    def handle_noargs(self, **options):
        self.storage = git_storage.GitStorage()
        self.repository = self.storage.repository

        self.known_blobs = set(models.BlobMetadata.objects.values_list('id', flat=True))

        self.sync_tree(self.repository.tree)
