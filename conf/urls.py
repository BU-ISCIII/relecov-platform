"""Root URL configuration with the standard deployment health endpoint."""

from django.urls import include, path

# BEGIN BU-ISCIII APPLICATION: django-url-imports
from django.contrib import admin

# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
# from drf_yasg.generators import OpenAPISchemaGenerator
from drf_spectacular.views import (
    SpectacularRedocView,
    SpectacularSwaggerView,
    SpectacularAPIView,
)

"""
class BothHttpAndHttpsSchemaGenerator(OpenAPISchemaGenerator):
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        schema.schemes = ["http", "https"]
        return schema


schema_view = get_schema_view(
    openapi.Info(
        title="RELECOV API",
        default_version="v0.0.1",
        description="Relecov Platform API",
    ),
    generator_class=BothHttpAndHttpsSchemaGenerator,
    public=True,
)
"""
# END BU-ISCIII APPLICATION: django-url-imports

urlpatterns = [
    # Required by Compose health checks and deployment smoke tests.
    path("health/", include("deployment_health.urls")),
    # BEGIN BU-ISCIII APPLICATION: django-url-routes
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("documentation/", include("docs.urls")),
    # API REST FULL using drf spectacular
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"
    ),
    path(
        "swagger/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"
    ),
    # REST FRAMEWORK URLS
    path("api/", include("core.api.urls")),
    # user accounts
    path("accounts/", include("django.contrib.auth.urls")),
    # path('markdownx/', include('markdownx.urls')),
    # END BU-ISCIII APPLICATION: django-url-routes
]
