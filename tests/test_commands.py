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
import io

from django.core.management import call_command
from django.test import TestCase

from gitstorage import models
from gitstorage import repository
from gitstorage.tests.utils import VanillaRepositoryMixin


class SyncBlobMedataTestCase(VanillaRepositoryMixin, TestCase):

    def test_sync(self):
        """Creating objects for new blobs."""
        repo = repository.Repository()

        self.assertQuerysetEqual(models.Blob.objects.all(), [])
        call_command("sync_blobs", "refs/heads/master", "0" * 40, str(repo.head.target), verbosity=0)
        blob = models.Blob.objects.get(id="257cc5642cb1a054f08cc83f2d943e56fd3ebe99")
        self.assertEqual(blob.size, 4)

    def test_idempotent(self):
        """Safely ignore blobs already treated."""
        repo = repository.Repository()

        call_command("sync_blobs", "refs/heads/master", "0" * 40, str(repo.head.target), verbosity=0)
        count = models.Blob.objects.count()
        call_command("sync_blobs", "refs/heads/master", "0" * 40, str(repo.head.target), verbosity=0)
        call_command("sync_blobs", "refs/heads/master", "0" * 40, str(repo.head.target), verbosity=0)
        self.assertEqual(models.Blob.objects.count(), count)

    def test_partial_sync(self):
        repository.Repository()

        call_command(
            "sync_blobs", "refs/heads/master",
            "0" * 40, "6780fb7f2ae0bced73f951e0d2dd6448a50a2318", verbosity=0,
        )
        # Two files in the initial commit
        self.assertEqual(models.Blob.objects.count(), 2)

        call_command(
            "sync_blobs", "refs/heads/master",
            "6780fb7f2ae0bced73f951e0d2dd6448a50a2318", "c56e723761909ea406790c946da307fd681fe647", verbosity=0,
        )
        # Added an (hidden) file
        self.assertEqual(models.Blob.objects.count(), 3)

        call_command(
            "sync_blobs", "refs/heads/master",
            "c56e723761909ea406790c946da307fd681fe647", "9c2c91388ca1b5b6e247038f2644493ff47f116e", verbosity=0,
        )
        # Added an empty file in an (hidden) directory (same OID, so no new object)
        self.assertEqual(models.Blob.objects.count(), 3)

        call_command(
            "sync_blobs", "refs/heads/master",
            "9c2c91388ca1b5b6e247038f2644493ff47f116e", "d104ab48cc867e89928e0094d192e5516a98dd25", verbosity=0,
        )
        # Added a (UTF-8 filename) file
        self.assertEqual(models.Blob.objects.count(), 4)

    def test_another_branch(self):
        """We're pushing to another branch on the repo."""
        repo = repository.Repository()
        # Make coverage happy by being silently verbose
        stdout, stderr = io.StringIO(), io.StringIO()

        self.assertQuerysetEqual(models.Blob.objects.all(), [])

        call_command(
            "sync_blobs", "refs/heads/branch", "0" * 40, str(repo.head.target), verbosity=1,
            stdout=stdout, stderr=stderr,
        )

        # Nothing done
        self.assertQuerysetEqual(models.Blob.objects.all(), [])

    def test_verbosity(self):
        """make coverage happy"""
        stdout, stderr = io.StringIO(), io.StringIO()

        repo = repository.Repository()
        call_command(
            "sync_blobs", "refs/heads/master", "0" * 40, str(repo.head.target), verbosity=2,
            stdout=stdout, stderr=stderr,
        )

        self.assertNotEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")
