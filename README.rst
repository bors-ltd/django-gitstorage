GitStorage
==========

A Django application to browse files in a Git repository and build Web applications on top of it.

The kind of repositories we target are hosting files, relatively big in size, and no commit history is considered.
GitStorage is not a collaboration tool, only easing downloading the files from a browser.

Files are served directly from the bare repository configured in the settings, no working copy is maintained.

GitStorage is:

- Unmanaged `models`_ to represent Git objects, and use them in templates.

- Mixin `views`_ to combine with class-based views to browse the repository and add or remove objects.
  on top of the repository;

- Permissions to access a given tree (folder).

GitStorage is built on top of `pygit2`_ and `libgit2`_, it does not call Git from the command line.

.. _`pygit2`: http://www.pygit2.org/

.. _`libgit2`: http://libgit2.github.com/


.. contents::

Models
------

Blob
""""

This unmanaged model represents a git object of type blob,
but that would know its filename from the parent tree.
The filename extension then gives us the mimetype associated.

Tree
""""

This unmanaged model represents a git object of type tree, which can be checked for
access permission.

TreePermission
""""""""""""""

Only super users are allowed by default. Share access to a tree and its blobs (but not its subtrees) to a regular user.

Anonymous users are supported too, with the idea of allowing access to individual blobs, rather than the whole tree.

Views
-----

These views are designed as the foundation of class-based views like TemplateView and FormView,
and your own business logic.

BaseRepositoryView
""""""""""""""""""

The catch-all view that dispatches to a view dedicated to each Git object type (only blob and tree).

This view will be your URL root, configured with a view for each object type (see below).

TreeViewMixin
"""""""""""""

Default view for a tree object, lists its contents, filtered by tree permissions.

BlobViewMixin
"""""""""""""

Default view for a blob object, displays its information, if allowed by access controls.

DownloadViewMixin
"""""""""""""""""

Force download the current blob's data.

Even content native to the browser, image or PDF, would be downloaded.

InlineViewMixin
"""""""""""""""

View the current blob's data in the browser if possible, download it otherwise.

It does not mean images are previewed at a smaller resolution.

SharesViewMixin
"""""""""""""""

List of current tree permissions and removing the selected ones.

ShareViewMixin
""""""""""""""

Share access to the current tree to a user by adding a tree permission.

Tests
-----

A minimal Django project is shipped to run the test suite. Try ``make coverage`` (100% at the time of this writing).

Migrations
----------

GitStorage comes with Django migrations.

License
-------

Copyright (C) 2013-2015,2017,2019  Bors LTD with ideas from the PyGit2 project.

Django-gitstorage is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
