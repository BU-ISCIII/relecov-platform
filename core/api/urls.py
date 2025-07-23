# Generic imports
from django.urls import path

# Local imports
import core.api.views

app_name = "relecov_api"


urlpatterns = [
    path(
        "createBioinfoData",
        core.api.views.create_bioinfo_metadata,
        name="create_bioinfo_data",
    ),
    path(
        "createSampleData",
        core.api.views.create_sample_data,
        name="create_sample_data",
    ),
    path(
        "createVariantData",
        core.api.views.create_variant_data,
        name="create_variant_data",
    ),
    path("updateState", core.api.views.update_state, name="update_state"),
    path(
        "checkSampleExists",
        core.api.views.check_sample_exists,
        name="check_sample_exists",
    ),
]
