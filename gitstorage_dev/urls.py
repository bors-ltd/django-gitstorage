from django.conf.urls import patterns, url

from .tests import views

urlpatterns = patterns('',
    # Blob views
    url(r'^(?P<path>.+)/;preview$', views.TestPreviewView.as_view(), name='blob_preview'),
    url(r'^(?P<path>.+)/;download$', views.TestDownloadView.as_view(), name='blob_download'),
    url(r'^(?P<path>.+)/;delete$', views.TestDeleteView.as_view(), name='blob_delete'),
    # Tree views (including the root)
    url(r'^(?P<path>.*)/?;shares$', views.TestSharesView.as_view(), name='tree_shares'),
    url(r'^(?P<path>.*)/?;share$', views.TestShareView.as_view(), name='tree_share'),
    url(r'^(?P<path>.*)/?;upload$', views.TestUploadView.as_view(), name='tree_upload'),
    # Browse/catch-all view
    url(r'^(?P<path>.*)$', views.TestRepositoryView.as_view(), name='repo_browse'),
)
