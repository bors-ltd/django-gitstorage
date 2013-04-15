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


def path_validator(path):
    if path:
        if path[0] == "/":
            raise ValidationError("absolute path forbidden")
        if path[0] == ".":
            raise ValidationError("relative path forbidden")


def name_validator(name):
    if name and "/" in name:
        raise ValidationError("path forbidden")
