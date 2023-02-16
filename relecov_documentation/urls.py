from django.urls import path
from django.conf import settings
from relecov_documentation import views
from django.conf.urls.static import static

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "relecovInstall/", views.relecov_install, name="relecov_install"
    ),
    path("configuration/", views.configuration, name="configuration"),

    path("metadata/", views.metadata, name="metadata"),
    path("metadataLabExcel/", views.metadata_lab_excel, name="metadata_lab_excel"),
    path("relecovTools/", views.relecov_tools, name="relecov_tools"),
    path("intranet/", views.intranet, name="intranet"),
    path("intranetDashboard/", views.intranet_dashboard, name="intranet_dashboard"),
    path(
        "uploadMetadataLab/", views.upload_metadata_lab, name="upload_metadata_lab"
        ),
    path("variantDashboard/", views.variant_dashboard, name="variant_dashboard"),
    path("methodologyDashboard/", views.methodology_dashboard, name="methodology_dashboard"),
    path("nextstrainInstall/", views.nextstrain_install, name="nextstrain_install"),
    path("howtoNextstrain/", views.howto_nextstrain, name="howto_nextstrain"),
    path("UploadToEna/", views.upload_to_ena, name="upload_to_ena"),
    path("UploadToGisaid/", views.upload_to_gisaid, name="upload_to_gisaid"),
    path("ApiSchema/", views.api_schema, name="api_schema"),
    path("HowtoApi/", views.howto_api, name="howto_api"),
    path(
        "createNewUser/",
        views.create_new_user,
        name="create_new_user",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
