# Generic imports
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Local imports
import docs.views

urlpatterns = [
    path("", docs.views.index, name="index"),
    path("description/", docs.views.description, name="description"),
    path(
        "relecov_install/",
        docs.views.relecov_install,
        name="relecov_install",
    ),
    path(
        "configuration/",
        docs.views.configuration,
        name="configuration",
    ),
    path("metadata/", docs.views.metadata, name="metadata"),
    path(
        "metadata_lab_excel/",
        docs.views.metadata_lab_excel,
        name="metadata_lab_excel",
    ),
    path("relecov_tools/", docs.views.relecov_tools, name="relecov_tools"),
    path(
        "intranet_overview/",
        docs.views.intranet_overview,
        name="intranet_overview",
    ),
    path(
        "intranet_contact_data/",
        docs.views.intranet_contact_data,
        name="intranet_contact_data",
    ),
    path(
        "intranet_sample_search/",
        docs.views.intranet_sample_search,
        name="intranet_sample_search",
    ),
    path(
        "intranet_received_samples/",
        docs.views.intranet_received_samples,
        name="intranet_received_samples",
    ),
    path(
        "intranet_upload_metadata/",
        docs.views.intranet_upload_metadata,
        name="intranet_upload_metadata",
    ),
    path(
        "variant_dashboard/",
        docs.views.variant_dashboard,
        name="variant_dashboard",
    ),
    path(
        "methodology_dashboard/",
        docs.views.methodology_dashboard,
        name="methodology_dashboard",
    ),
    path(
        "nextstrain_install/",
        docs.views.nextstrain_install,
        name="nextstrain_install",
    ),
    path(
        "howto_nextstrain/",
        docs.views.howto_nextstrain,
        name="howto_nextstrain",
    ),
    path("upload_to_ena/", docs.views.upload_to_ena, name="upload_to_ena"),
    path(
        "upload_to_gisaid/",
        docs.views.upload_to_gisaid,
        name="upload_to_gisaid",
    ),
    path("api_schema/", docs.views.api_schema, name="api_schema"),
    path("howto_api/", docs.views.howto_api, name="howto_api"),
    path(
        "create_new_user/",
        docs.views.create_new_user,
        name="create_new_user",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
