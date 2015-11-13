GitStorage
==========

A Django application to browse a Git repository and build Web applications on top of it.

GitStorage is:

- A Django `storage`_ to browse the contents of the repository (what you see in your working copy)
  from a bare repository (without a working copy);

- `Models`_ to enrich Git objects, namely add metadata to blobs and allow access to trees;

- Mixin `views`_ to combine with class-based views to browse the repository and add or remove objects.
  on top of the repository;

- `Management commands`_;

- `Hooks`_.

GitStorage is built on top of `PyGit2`_ and `libgit2`_, it does not call Git from the command line.

.. _`PyGit2`: http://www.pygit2.org/

.. _`libgit2`: http://libgit2.github.com/

.. contents::

Storage
-------

The Django storage supports most of the storage API: open, save, exists, listdir... missing features include mtime,
ctime and atime since Git doesn't directly store those values.

The storage is limited just as any Git repository. It is designed for a single writer and many readers. Concurrent
writing is not even tested. No effort was made to optimise read access either. Your mileage may vary.

The storage exposes trees and blobs, and doesn't try to pretend you see dirs and files on a regular filesystem.

Models
------

BlobMetadata
""""""""""""

Add metadata to the blob, only mimetype for now.

TreePermission
""""""""""""""

Only admin users are allowed by default. Share access to a tree and its blobs (but not its subtrees) to a regular user.

Views
-----

These views are designed as the foundation of class-based views like TemplateView and FormView,
and your own business logic.

BaseRepositoryView
""""""""""""""""""

The main view that dispatches to a view dedicated to each Git object type (namely blob and tree).

The view you will hook on your URL root, with configuring a view for each object type (see below).

TreeViewMixin
"""""""""""""

Default view for a tree object, lists its contents.

BlobViewMixin
"""""""""""""

Default view for a blob object, displays its information.

PreviewViewMixin
""""""""""""""""

Preview the current blob in the browser if possible, download it otherwise.

DownloadViewMixin
"""""""""""""""""

Force download the current blob.

DeleteViewMixin
"""""""""""""""

Delete the current blob.

UploadViewMixin
"""""""""""""""

Upload a new file to the current tree (as a blob).

SharesViewMixin
"""""""""""""""

List of current tree permissions and removing the selected ones.

ShareViewMixin
""""""""""""""

Share access to the current tree to a user by adding a tree permission.

Management Commands
-------------------

sync_blobmetadata
"""""""""""""""""

Browse the repository to compute metadata for each blob not known yet.

Called by the "update" hook you need to add to your repository (see `Hooks`_).

Cleaning up of metadata for orphan blobs is not handled.

Tests
-----

A minimal Django project is shipped to run the test suite. Try ``make coverage`` (100% at the time of this writing).

Migrations
----------

GitStorage comes with migrations in the new 1.7+ format.

Hooks
-----

Gitstorage requires metadata to be created for each blob. Copy ``hooks/update`` to the hooks directory of your
repository and edit the "VENV" and "DJANGO_SETTINGS_MODULE" variables. You are advised to set "verbose" to true for the first tries.
In fact, feel free to edit this script to suit your needs and deployment of the Django project.

License
-------

GitStorage is copyright Bors LTD with ideas from the PyGit2 project.

GitStorage is published under the GNU General Public License version 3.
