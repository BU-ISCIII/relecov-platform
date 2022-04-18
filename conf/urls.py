from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(openapi.Info(
    title="iSkyLIMS API",
    default_version='v0.0.1',
    description="iSkyLIMS API",
    ),
    public=True,
)

urlpatterns = [
<<<<<<< HEAD
    path('admin/', admin.site.urls),
    path('', include('relecov_core.urls')),
    path('dashboard/', include("relecov_dashboard.urls")),

    # REST FRAMEWORK URLS
    path('api/', include('relecov_core.api.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0))
=======
    path("admin/", admin.site.urls),
    path("", include("relecov_core.urls")),
    path("dashboard/", include("relecov_dashboard.urls")),
>>>>>>> 57b9202c7d74df38380b579878126d99d7d5636b
]
