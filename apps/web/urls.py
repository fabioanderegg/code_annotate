from django.conf.urls import url

from . import views

urlpatterns = [
    url('^browse/(?P<path>.*)$', views.BrowseView.as_view(), name='browse'),
    url('^annotate/(?P<path>.*)$', views.AnnotateView.as_view(), name='annotate'),
]
