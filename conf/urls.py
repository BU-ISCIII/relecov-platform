from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from drf_yasg.generators import OpenAPISchemaGenerator


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


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("relecov_core.urls")),
    path("dashboard/", include("relecov_dashboard.urls")),
    path("documentation/", include("relecov_documentation.urls")),
    # REST FRAMEWORK URLS
    path("api/", include("relecov_core.api.urls")),
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0)),
    # user accounts
    path("accounts/", include("django.contrib.auth.urls")),
    # path('markdownx/', include('markdownx.urls')),
]
