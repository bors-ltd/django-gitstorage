from django.conf.urls import url

from . import views

urlpatterns = [
    # Blob views
    url(r'^(?P<path>.+)/;inline', views.TestInlineView.as_view(), name='blob_inline'),
    url(r'^(?P<path>.+)/;download$', views.TestDownloadView.as_view(), name='blob_download'),
    # Tree views (including the root)
    url(r'^(?P<path>.*)/?;shares$', views.TestSharesView.as_view(), name='tree_shares'),
    url(r'^(?P<path>.*)/?;share$', views.TestShareView.as_view(), name='tree_share'),
    # Browse/catch-all view
    url(r'^(?P<path>.*)$', views.TestRepositoryView.as_view(), name='repo_browse'),
]
