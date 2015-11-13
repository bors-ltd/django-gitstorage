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

from django.core.management import call_command
from django.test import TestCase

from gitstorage import models
from gitstorage import wrappers
from gitstorage.tests.utils import VanillaRepositoryMixin


class SyncBlobMedataTestCase(VanillaRepositoryMixin, TestCase):

    def test_sync(self):
        repository = wrappers.Repository(self.location)

        self.assertQuerysetEqual(models.BlobMetadata.objects.all(), [])
        call_command("sync_blobmetadata", "refs/heads/master", "0" * 40, str(repository.head.target), verbosity=0)
        metadata = models.BlobMetadata.objects.get(id="257cc5642cb1a054f08cc83f2d943e56fd3ebe99")
        self.assertEqual(metadata.mimetype, "text/plain")

    def test_idempotent(self):
        repository = wrappers.Repository(self.location)

        call_command("sync_blobmetadata", "refs/heads/master", "0" * 40, str(repository.head.target), verbosity=0)
        count = models.BlobMetadata.objects.count()
        call_command("sync_blobmetadata", "refs/heads/master", "0" * 40, str(repository.head.target), verbosity=0)
        call_command("sync_blobmetadata", "refs/heads/master", "0" * 40, str(repository.head.target), verbosity=0)
        self.assertEqual(models.BlobMetadata.objects.count(), count)
