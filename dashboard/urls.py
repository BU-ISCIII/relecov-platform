# Generic imports
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

# Local imports
import dashboard.views

urlpatterns = [
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
    # Methodology graphics
    path(
        "methodology",
        dashboard.views.methodology_index,
        name="methodology_index",
    ),
    path(
        "methodology/hostInfo",
        dashboard.views.methodology_host_info,
        name="methodology_host_info",
    ),
    path(
        "methodology/sequencing",
        dashboard.views.methodology_sequencing,
        name="methodology_sequencing",
    ),
    path(
        "methodology/sampleProcessing",
        dashboard.views.methodology_sample_processing,
        name="methodology_sample_processing",
    ),
    path(
        "methodology/bioinfo",
        dashboard.views.methodology_bioinfo,
        name="methodology_bioinfo",
    ),
    path("variants", dashboard.views.variants_index, name="variants_index"),
    path(
        "variants/mutationsInLineage",
        dashboard.views.mutations_in_lineage,
        name="mutations_in_lineage",
    ),
    path(
        "variants/spikeMutations3d",
        dashboard.views.spike_mutations_3d,
        name="spike_mutations_3d",
    ),
    path(
        "variants/lineagesVoc",
        dashboard.views.lineages_voc,
        name="lineages_voc",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
