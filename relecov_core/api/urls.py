from django.urls import path
from relecov_core.api import views

app_name = "relecov_api"


urlpatterns = [
    path("test/", views.test, name="test"),
]
