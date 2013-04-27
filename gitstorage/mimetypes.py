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

"""
Preload and complement the Python mimetypes module.
"""

from __future__ import absolute_import, print_function, unicode_literals

import mimetypes

mimetypes.init()
for mimetype, ext in [("image/x-xcf", ".xcf")]:
    mimetypes.add_type(mimetype, ext)

__all__ = ['guess_type']


def guess_type(url, strict=False):
    return mimetypes.guess_type(url, strict=strict)
