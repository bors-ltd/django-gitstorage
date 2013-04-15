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

from django.test import TestCase

from ..utils import Path


class PathTestCase(TestCase):

    def test_path_unicode(self):
        path = Path("my/path")
        self.assertEqual(path.parent_path, "my")
        self.assertEqual(path.name, "path")

    def test_path_str(self):
        path = Path(b'my/path')
        self.assertEqual(path.parent_path, "my")
        self.assertEqual(path.name, "path")

    def test_path_root(self):
        path = Path("")
        self.assertEqual(path.parent_path, "")
        self.assertEqual(path.name, "")

    def test_resolve(self):
        path = Path("my/path")
        self.assertEqual(path.resolve("name"), "my/path/name")

    def test_resolve_str(self):
        path = Path("my/path")
        self.assertEqual(path.resolve(b"name"), "my/path/name")

    def test_resolve_root(self):
        path = Path("")
        self.assertEqual(path.resolve("name"), "name")
