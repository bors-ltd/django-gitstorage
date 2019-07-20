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

from django.test import TestCase

from gitstorage.utils import Path


class PathTestCase(TestCase):

    def test_path_str(self):
        path = Path("my/path")
        self.assertEqual(path.parent_path, "my")
        self.assertEqual(path.name, "path")

    def test_path_bytes(self):
        path = Path(b'my/path')
        self.assertEqual(path.parent_path, "my")
        self.assertEqual(path.name, "path")

    def test_path_root(self):
        path = Path("")
        self.assertEqual(path.parent_path, "")
        self.assertEqual(path.name, "")

    def test_resolve_str(self):
        path = Path("my/path")
        self.assertEqual(path.resolve("name"), "my/path/name")

    def test_resolve_bytes(self):
        path = Path("my/path")
        self.assertEqual(path.resolve(b"name"), "my/path/name")

    def test_resolve_root(self):
        path = Path("")
        self.assertEqual(path.resolve("name"), "name")
