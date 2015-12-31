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

- `Git hooks`_.

GitStorage is built on top of `pygit2`_ and `libgit2`_, it does not call Git from the command line.

.. _`pygit2`: http://www.pygit2.org/

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

Add metadata to the blob, only mimetype for now. We also store a copy of the size, so we don't have to load the blob
(and its data) for it.

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

PreviewViewMixin
""""""""""""""""

Preview the current blob data in the browser if possible, download it otherwise.

Previewing an image could mean returning a smaller (in size and weight) image.

DownloadViewMixin
"""""""""""""""""

Force download the current blob's data.

For our image example, it would mean downloading the original image, not the smaller preview.

DeleteViewMixin
"""""""""""""""

Delete the current blob from its parent tree (it could still be referenced elsewhere).

UploadViewMixin
"""""""""""""""

Upload a new file to the current tree (in a blob).

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

Called by the "update" hook you need to add to your repository (see `Git Hooks`_).

Browse the given range of commits to compute metadata for each referenced blob not known yet.

Cleaning up of metadata for orphan blobs is not handled.

Tests
-----

A minimal Django project is shipped to run the test suite. Try ``make coverage`` (100% at the time of this writing).

Migrations
----------

GitStorage comes with migrations in the new 1.7+ format.

Git Hooks
---------

Gitstorage requires metadata to be created for each blob. Copy ``hooks/update`` to the hooks directory of your
repository and edit the "VENV" and "DJANGO_SETTINGS_MODULE" variables. Make sure the script has the executable bit.

You are advised to set "verbose" to true for the first tries.

In fact, feel free to edit this script to suit your needs and deployment of the Django project.

License
-------

GitStorage is copyright Bors LTD with ideas from the PyGit2 project.

GitStorage is published under the GNU General Public License version 3.
