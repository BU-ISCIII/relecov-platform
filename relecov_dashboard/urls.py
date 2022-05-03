from django.urls import path, include
from django.conf import settings

from . import views
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("methodology", views.methodology_index, name="methodology_index"),
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, 
        document_root=settings.MEDIA_ROOT
    )
