from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from example.example_app.views import the_view

urlpatterns = [
    path("", the_view),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
