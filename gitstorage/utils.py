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


class Path(str):
    """Path string that knows its path and name parts.

    Think of the shell's dirname and basename.
    """
    parent_path = None
    name = None

    def __new__(cls, path):
        if isinstance(path, bytes):
            path = path.decode('utf8')  # Git encoding

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
        path = str.__new__(cls,  "/".join(segments))

        # Attach properties
        path.parent_path = parent_path
        path.name = name

        return path

    def resolve(self, name):
        """Join the path and a name, always with "/" for Git."""
        if isinstance(name, bytes):
            name = name.decode('utf8')  # Git encoding
        if self:
            return self + "/" + name
        # Root
        return name
