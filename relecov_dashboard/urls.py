from django.urls import path, include
from django.conf import settings

from . import views
from django.conf.urls.static import static

urlpatterns = [
    path("variantDashboard", views.variant_dashboard, name="variant_dashboard"),
    path("methodologyDashboard", views.methodology_dashboard, name="methodology_dashboard"),
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
    # path("needlePlot", views.needle_plot, name="needle_plot"),
    # path("molecular3D", views.molecular_3D, name="molecular_3D"),
    # path("", views.dashboard, name="dashboard"),
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
