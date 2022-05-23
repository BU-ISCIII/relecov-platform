from django.urls import path
from relecov_core.api import views

app_name = "relecov_api"


urlpatterns = [
    path("test/", views.test, name="test"),
    path("createSample", views.create_sample_data, name="create_sample_data"),
    path("analysisData", views.analysis_data, name="analysis_data"),
]
