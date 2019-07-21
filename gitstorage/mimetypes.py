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

"""
Preload and complement the Python mimetypes module.
"""

import mimetypes

mimetypes.init()
for mimetype, ext in [
    ("image/x-xcf", ".xcf"),
    ("image/x-pentax-pef", ".pef"),
    ("image/x-panasonic-rw2", ".rw2"),
]:
    mimetypes.add_type(mimetype, ext)

__all__ = ["guess_type"]


def guess_type(url, strict=False):
    return mimetypes.guess_type(url, strict=strict)
