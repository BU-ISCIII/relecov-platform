from django.urls import path
from relecov_core.api import views

app_name = "relecov_api"


urlpatterns = [
    path(
        "createBioinfoData", views.create_bioinfo_metadata, name="create_bioinfo_data"
    ),
    path("createSampleData", views.create_sample_data, name="create_sample_data"),
    path("createbioinfoData", views.create_bioinfo_metadata_file, name="create_bioinfo_data"),
    path("createVariantData/", views.create_variant_data, name="create_variant_data"),
    path("updateState/", views.update_state, name="update_state"),
    path("accessionEna/", views.accession_ena, name="accession_ena"),
]
