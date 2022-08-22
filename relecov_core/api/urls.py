from django.urls import path
from relecov_core.api import views

app_name = "relecov_api"


urlpatterns = [
    path("analysisData", views.analysis_data, name="analysis_data"),
    path("createSampleData", views.create_sample_data, name="create_sample_data"),
    path("longtableData", views.longtable_data, name="longtable_data"),
    path("bioinfoData", views.bioinfo_metadata_file, name="bioinfo_data"),
    path("updateState/", views.update_state, name="update_state"),
    path("accessionEna/", views.accession_ena, name="accession_ena"),
    path("batchSample/", views.batch_sample, name="batch_sample"),
]
