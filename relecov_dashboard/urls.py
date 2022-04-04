from django.urls import path, include
from django.conf import settings

from . import views
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("2", views.index2, name="index2"),
    path("3", views.index3, name="index3"),
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
