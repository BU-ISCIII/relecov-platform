from django.urls import path, include
from django.conf import settings

from . import views
from django.conf.urls.static import static

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("lineagesInTime", views.lineages_in_time, name="lineages_in_time"),
    path("methodology", views.methodology_index, name="methodology_index"),
    path("needlePlot", views.needle_plot, name="needle_plot"),
    path("molecular3D", views.molecular_3D, name="molecular_3D"),
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
