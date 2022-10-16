from django.urls import path
from django.conf import settings
from relecov_documentation import views
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "createUserAccount/",
        views.create_user_account,
        name="create_user_account",
    ),
    path(
        "initialConfiguration",
        views.initial_configuration,
        name="initial_configuration",
    ),
    path("installation/", views.installation, name="installation"),
    path("intranet/", views.intranet, name="intranet"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("metadataLabForm/", views.upload_metadata_lab, name="upload_metadata_lab"),
    path("UploadToEna/", views.upload_to_ena, name="upload_to_ena"),
    path("UploadToGisaid/", views.upload_to_gisaid, name="upload_to_gisaid"),
    path("ApiUsage/", views.api_usage, name="api_usage"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
