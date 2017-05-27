GitStorage
==========

A Django application to browse a Git repository and build Web applications on top of it.

GitStorage is:

- A `Git hook`_ to fill the database when pushing to the repository;

- `Models`_ to represent and enrich Git objects, adding extra fields to blobs and allow access to trees;

- Mixin `views`_ to combine with class-based views to browse the repository and add or remove objects.
  on top of the repository;

GitStorage is built on top of `pygit2`_ and `libgit2`_, it does not call Git from the command line.

.. _`pygit2`: http://www.pygit2.org/

.. _`libgit2`: http://libgit2.github.com/

Hopefully some day Git database backends will be more easily accessible with Python wrappers,
and this project will become a lot simpler.


.. contents::

Git Hook
--------

The journey starts with the ``hooks/update`` hook to install into the repository being exposed.

When objects are pushed to this repository, it will call a management command to fill the database with
new blobs and compute their extra fields.

Copy the script to the hooks directory of your repository and edit the "VENV" and "DJANGO_SETTINGS_MODULE" variables.
Make sure the script has the executable bit.

You are advised to set "verbose" to true for the first tries.

In fact, feel free to edit this script to suit your needs and deployment constraints.

Models
------

Blob
""""

Git object of type blob with extra fields possible. We store the data in a filesystem storage,
so this file can be opened by any regular tool for extra transformation: metadata extraction, thumbnails...
The storage also provides an internal URL for the front-end web server to serve it (X-Accel-Redirect).

We ignore all other object types.

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

Management Command
------------------

sync_blobs
""""""""""

Called by the "update" hook you need to add to your repository (see `Git Hook`_).

Browse the given range of commits to created missing blobs and compute their extra fields.

Cleaning up of orphan blobs is not handled.

Tests
-----

A minimal Django project is shipped to run the test suite. Try ``make coverage`` (100% at the time of this writing).

Migrations
----------

GitStorage comes with Django migrations.

License
-------

GitStorage is copyright Bors LTD with ideas from the PyGit2 project.

GitStorage is published under the GNU General Public License version 3.
