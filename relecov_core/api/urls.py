from django.urls import path
from relecov_core.api import views

app_name = "relecov_api"


urlpatterns = [
    path("analysisData", views.analysis_data, name="analysis_data"),
    path("createSampleData", views.create_sample_data, name="create_sample_data"),
    path("longtableData/", views.longtable_data, name="longtable_data"),
]
