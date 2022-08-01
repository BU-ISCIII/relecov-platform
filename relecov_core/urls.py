from django.urls import path
from django.conf import settings
from relecov_core import views
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("bioInfoHandling", views.bio_info_json_handling, name="bioInfo_handling"),
    path("Contact", views.contact, name="contact"),
    path("contributorInfo/", views.contributor_info, name="contributorInfo"),
    path("intranet/", views.intranet, name="intranet"),
    path("metadataForm", views.metadata_form, name="metadataForm"),
    path(
        "metadataVisualization/",
        views.metadata_visualization,
        name="metadataVisualization",
    ),
    path("relecovProject", views.relecov_project, name="relecov_project"),
    path(
        "resultsInfoProcessed/",
        views.results_info_processed,
        name="resultsInfoProcessed",
    ),
    path(
        "resultsInfoReceived/", views.results_info_received, name="resultsInfoReceived"
    ),
    path("resultsDownload/", views.results_download, name="resultsDownload"),
    path("sampleDisplay=<int:sample_id>", views.sample_display, name="sample_display"),
    path("schemaDisplay=<int:schema_id>", views.schema_display, name="schema_display"),
    path("schemaHandling", views.schema_handling, name="schema_handling"),
    path("searchSample", views.search_sample, name="search_sample"),
    path("uploadStatus/", views.upload_status, name="uploadStatus"),
    path("uploadStatusToENA/", views.upload_status_to_ENA, name="uploadStatusToENA"),
    path(
        "uploadStatusToGISAID/",
        views.upload_status_to_GISAID,
        name="uploadStatusToGISAID",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
