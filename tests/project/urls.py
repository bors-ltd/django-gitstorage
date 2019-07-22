from django.urls import path, re_path

from . import views

urlpatterns = [
    # Blob views
    path("<path:path>/;inline", views.TestInlineView.as_view(), name="blob_inline"),
    path(
        "<path:path>/;download", views.TestDownloadView.as_view(), name="blob_download"
    ),
    # Tree views (including the root)
    # Don't use the path converter, the empty string is a valid path
    re_path(
        r"^(?P<path>.*)/;shares$", views.TestSharesView.as_view(), name="tree_shares"
    ),
    re_path(r"^(?P<path>.*)/;share$", views.TestShareView.as_view(), name="tree_share"),
    # Browse/catch-all view
    re_path(r"^(?P<path>.*)$", views.TestRepositoryView.as_view(), name="repo_browse"),
]
