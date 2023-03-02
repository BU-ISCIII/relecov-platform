from django.urls import path, include
from django.conf import settings

from relecov_dashboard import views
from django.conf.urls.static import static

urlpatterns = [
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
    # Methodology graphics
    path("methodology", views.methodology_index, name="methodology_index"),
    path(
        "methodology/hostInfo",
        views.methodology_host_info,
        name="methodology_host_info",
    ),
    path(
        "methodology/sequencing",
        views.methodology_sequencing,
        name="methodology_sequencing",
    ),
    path(
        "methodology/bioinfo",
        views.methodology_bioinfo,
        name="methodology_bioinfo",
    ),
    path("variants", views.variants_index, name="variants_index"),
    path(
        "variants/receivedSamples",
        views.received_samples,
        name="received_samples",
    ),
    path(
        "variants/mutationsInLineage",
        views.mutations_in_lineage,
        name="mutations_in_lineage",
    ),
    path(
        "variants/spikeMutations3d",
        views.spike_mutations_3d,
        name="spike_mutations_3d",
    ),
    path(
        "variants/lineagesVoc",
        views.lineages_voc,
        name="lineages_voc",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
