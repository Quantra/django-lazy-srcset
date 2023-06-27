import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from example.example_app.views import the_view

urlpatterns = [
    path("__debug__/", include(debug_toolbar.urls)),
    path("", the_view),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
