# -*- coding: utf-8 -*-
# Copyright 2013 Bors Ltd
# This file is part of django-gitstorage.
#
#    django-gitstorage is free software: you can redistribute it and/or modify
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

import datetime

import pygit2


EPOCH = datetime.datetime(1970, 1, 1)

ST_FILE_MODE = 0o100600
ST_TREE_MODE = 0o40000


def make_signature(name, email, tz=None):
    """Generate a Signature object with the given user name and e-mail.

    The time is set to now() in Django's current timezone. User name is encoded to UTF-8.

        @param name: user full name
        @param email: user e-mail
        @return: pygit2.Signature()
    """
    now = datetime.datetime.utcnow()
    timestamp = int((now - EPOCH).total_seconds())  # XXX Python 2.7
    # Offset in minutes
    offset = int(tz.utcoffset(now).total_seconds() // 60) if tz else 0
    return pygit2.Signature(name,
                            email,
                            timestamp,
                            offset)


class Path(unicode):
    parent_path = None
    name = None

    def __new__(cls, path):
        # Filter out leading and trailing "/"
        segments = [segment for segment in path.split("/") if segment]

        # Isolate name (base name) but keep it in the path
        name = ""
        if segments:
            name = segments.pop()

        parent_path = "/".join(segments)

        # Reconstruct the cleaned path
        if name:
            segments.append(name)
        path = unicode.__new__(cls,  "/".join(segments))

        # Attach properties
        path.parent_path = parent_path
        path.name = name

        return path

    def resolve(self, name):
        """Join the path and a name, always with "/" for Git."""
        if isinstance(name, str):
            name = name.decode('utf8')
        if self:
            return self + "/" + name
        # Root
        return name
