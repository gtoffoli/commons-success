"""success URL Configuration
"""
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib.flatpages import views as flatpages_views

from . import views
import commons.views

urlpatterns = [
    url(r"^$", views.home, name="success.home"),
    url(r'^', include('commons.urls')),
]

urlpatterns += i18n_patterns(
    url(r"^project/(?P<project_slug>[\w-]+)/$", commons.views.project_detail_by_slug, name="project_detail"),
    url(r"^repo/(?P<repo_slug>[\w-]+)/$", commons.views.repo_detail_by_slug, name="repo_detail"),
    url(r"^oer/(?P<oer_slug>[\w\d-]+)/$", commons.views.oer_detail_by_slug, name="oer_detail"),
    url(r"^lp/(?P<lp_slug>[\w\d-]+)/$", commons.views.lp_detail_by_slug, name="lp_detail"),
    url(r"^lp/(?P<lp_slug>[\w\d-]+)/download/$", commons.views.lp_download_by_slug, name="lp_download"),
    url(r"^pathnode/(?P<node_id>[\d-]+)/$", commons.views.pathnode_detail, name="pathnode_detail"),
    url(r'^(?P<url>.*)$', flatpages_views.flatpage, name='django.contrib.flatpages.views.flatpage'),
)
