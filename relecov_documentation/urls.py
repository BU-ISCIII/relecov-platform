from django.urls import path
from django.conf import settings
from relecov_documentation import views
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path("description", views.description, name="description"),
    path("relecovInstall/", views.relecov_install, name="relecov_install"),
    path("configuration/", views.configuration, name="configuration"),
    path("metadata/", views.metadata, name="metadata"),
    path("metadataLabExcel/", views.metadata_lab_excel, name="metadata_lab_excel"),
    path("relecovTools/", views.relecov_tools, name="relecov_tools"),
    path("intranetOverview/", views.intranet_overview, name="intranet_overview"),
    path(
        "intranetContactData/",
        views.intranet_contact_data,
        name="intranet_contact_data",
    ),
    path(
        "intranetSampleSearch/",
        views.intranet_sample_search,
        name="intranet_sample_search",
    ),
    path(
        "intranetReceivedSamples/",
        views.intranet_received_samples,
        name="intranet_received_samples",
    ),
    path(
        "intranetUploadMetadata/",
        views.intranet_upload_metadata,
        name="intranet_upload_metadata",
    ),
    path("variantDashboard/", views.variant_dashboard, name="variant_dashboard"),
    path(
        "methodologyDashboard/",
        views.methodology_dashboard,
        name="methodology_dashboard",
    ),
    path("nextstrainInstall/", views.nextstrain_install, name="nextstrain_install"),
    path("howtoNextstrain/", views.howto_nextstrain, name="howto_nextstrain"),
    path("uploadToEna/", views.upload_to_ena, name="upload_to_ena"),
    path("uploadToGisaid/", views.upload_to_gisaid, name="upload_to_gisaid"),
    path("apiSchema/", views.api_schema, name="api_schema"),
    path("howtoApi/", views.howto_api, name="howto_api"),
    path(
        "createNewUser/",
        views.create_new_user,
        name="create_new_user",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
