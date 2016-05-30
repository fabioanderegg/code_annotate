from django.conf.urls import *  # NOQA
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from django.conf import settings
import django.views.static

admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
]

# This is only needed when using runserver.
if settings.DEBUG:
    urlpatterns = [
        url(r'^media/(?P<path>.*)$', django.views.static.serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
    ] + staticfiles_urlpatterns() + urlpatterns
