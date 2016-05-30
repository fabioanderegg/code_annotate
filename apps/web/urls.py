from django.conf.urls import url

from . import views

urlpatterns = [
    url('^browse/$', views.BrowseView.as_view(), name='browse'),
    url('^annotate/$', views.AnnotateView.as_view(), name='annotate'),
]
