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

from django.core.exceptions import ValidationError
from django.test import TestCase

from .. import validators


class PathValidatorTestCase(TestCase):

    def test_validator(self):
        self.assertIsNone(validators.path_validator("my/path"))

    def test_root(self):
        self.assertRaises(ValidationError, validators.path_validator, "/my/path")

    def test_relative(self):
        self.assertRaises(ValidationError, validators.path_validator, "./my/path")
        self.assertRaises(ValidationError, validators.path_validator, "../my/path")


class NameValidator(TestCase):

    def test_validator(self):
        self.assertIsNone(validators.name_validator("my_name"))

    def test_path(self):
        self.assertRaises(ValidationError, validators.name_validator, "/my_name")
        self.assertRaises(ValidationError, validators.name_validator, "my/name")
        self.assertRaises(ValidationError, validators.name_validator, "my_name/")
