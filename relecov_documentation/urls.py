from django.urls import path
from django.conf import settings
from relecov_documentation import views
from django.conf.urls.static import static

from django.urls import include

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
    path("Installation/", views.installation, name="installation"),
    path("Intranet/", views.intranet, name="intranet"),
    path("Dashboard/", views.dashboard, name="dashboard"),
    path("markdownx/", include("markdownx.urls")),
    path("UploadMetadataLab/", views.upload_metadata_lab, name="upload_metadata_lab"),
    path("ResultsDownload/", views.results_download, name="results_download"),
    path(
        "ResultsInfoProcessed/",
        views.results_info_processed,
        name="results_info_processed",
    ),
    path(
        "ResultsInfoReceived/",
        views.results_info_received,
        name="results_info_received",
    ),
    path("UploadToEna/", views.upload_to_ena, name="upload_to_ena"),
    path("UploadToGisaid/", views.upload_to_gisaid, name="upload_to_gisaid"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
