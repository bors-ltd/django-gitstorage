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

from django.core.management.base import BaseCommand

import pygit2

from gitstorage import models
from gitstorage import storage as git_storage


class Command(BaseCommand):
    help = "Compute metadata for new blobs (called from the update hook)."

    def add_arguments(self, parser):
        # These are the arguments the "update" hook will send
        parser.add_argument('refname', help='reference name (usually "refs/heads/master")')
        parser.add_argument('start_oid', help="start commit id (hash)")
        parser.add_argument('end_oid', help="end commit id (hash)")

    def sync_tree(self, repository, tree, known_blobs):
        """Recursively traverse a tree and create metadata for every of its blobs."""
        for entry in tree:
            if entry.type == "tree":
                self.sync_tree(repository, repository[entry.id], known_blobs)
            elif entry.type == "blob":
                if entry.hex in known_blobs:
                    continue
                blob = repository[entry.id]
                metadata = models.get_blob_metadata_model()(id=entry.hex)
                metadata.save()
                # Now we have saved, the instance have an ID for relations
                metadata.fill(repository, entry.name, blob)
                metadata.save()
                known_blobs.add(entry.hex)

    def walk(self, repository, start_oid, end_oid, known_blobs):
        """Walk the history from the head to the last known commit."""
        for commit in repository.walk(end_oid, pygit2.GIT_SORT_TOPOLOGICAL):
            if int(start_oid, 16) and commit.hex == start_oid:
                # Unless we give the fake parent of the initial commit ("0000...") we stop at the start commit
                # that should already be synced.
                # If we give "000..." as the start, walk entirely to synchronise the repository completely.
                return
            self.sync_tree(repository, commit.tree, known_blobs)

    def handle(self, **options):
        storage = git_storage.GitStorage()
        repository = storage.repository

        # Safely ignore pushing to another branch
        if repository.head.name != options['refname']:
            if options['verbosity']:
                self.stdout.write('Ignoring unexposed branch "{}", exiting.'.format(options['refname']))
            return

        known_blobs = set(models.get_blob_metadata_model().objects.values_list('id', flat=True))
        counter_before = len(known_blobs)

        start_oid = options['start_oid']
        end_oid = options['end_oid']
        if options['verbosity']:
            self.stdout.write("Synchronising metadata from {} to {}...".format(start_oid, end_oid))

        self.walk(repository, start_oid, end_oid, known_blobs)

        if options['verbosity']:
            counter_after = len(known_blobs)
            self.stdout.write("Done, {} metadata created.".format(counter_after - counter_before))
