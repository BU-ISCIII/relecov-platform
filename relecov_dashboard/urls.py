from django.urls import path, include
from django.conf import settings

from relecov_dashboard import views
from django.conf.urls.static import static

urlpatterns = [
    #path("django_plotly_dash/", include("django_plotly_dash.urls")),
    # Methodology graphics
    path("methodology", views.methodology_index, name="methodology_index"),
    path(
        "methodology/hostInfo",
        views.methodology_host_info,
        name="methodology_host_info",
    ),
    path(
        "methodology/sampleProcessing",
        views.methodology_sample_processing,
        name="methodology_sample_processing",
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
        "variants/receivedSamplesDashboard",
        views.received_samples_dashboard,
        name="received_samples_dashboard",
    ),
    path(
        "variants/mutationsInLineagesDashboard",
        views.mutations_in_lineages_dashboard,
        name="mutations_in_lineages_dashboard",
    ),
    path(
        "variants/spikeMutations3dDashboard",
        views.spike_mutations_3d_dashboard,
        name="spike_mutations_3d_dashboard",
    ),
    path(
        "variants/lineagesVocDashboard",
        views.lineages_voc_dashboard,
        name="lineages_voc_dashboard",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
