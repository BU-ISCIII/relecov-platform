from django.urls import path, include
from django.conf import settings

from relecov_dashboard import views
from django.conf.urls.static import static

urlpatterns = [
    path("variantDashboard", views.variant_dashboard, name="variant_dashboard"),
    path(
        "methodologyDashboard",
        views.methodology_dashboard,
        name="methodology_dashboard",
    ),
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
    path("lineagesVOC", views.lineages_voc, name="lineages_voc"),
    path("hackatonGraphs", views.hackaton_graphs, name="hackaton_graphs"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
