from django.urls import path, include
from django.conf import settings

from relecov_dashboard import views
from django.conf.urls.static import static

urlpatterns = [
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
    path("variants", views.variants_index, name="variants_index"),
    path(
        "variants/lineagesDashboard",
        views.lineages_dashboard,
        name="lineages_dashboard",
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
    path(
        "variants/mutationsInLineagesBySample",
        views.mutations_in_lineages_by_samples,
        name="variants_mutations_in_lineages_needle_plot",
    ),
    path(
        "variants/mutationsInLineagesByLineage",
        views.mutations_in_lineages_by_lineage,
        name="mutations_in_lineages_by_lineage",
    ),
    path(
        "variants/mutationsInLineagesHeatmap",
        views.variants_mutations_in_lineages_heatmap,
        name="variants_mutations_in_lineages_heatmap",
    ),
    path(
        "variants/mutationsInLineagesTable",
        views.variants_mutations_in_lineages_table,
        name="variants_mutations_in_lineages_table",
    ),
    path(
        "variants/samplesReceivedOverTimeGraph",
        views.samples_received_over_time_graph,
        name="variants_lineage_variation_over_time_graph",
    ),
    path(
        "variants/samplesReceivedOverTimeMap",
        views.samples_received_over_time_map,
        name="samples_received_over_time_map",
    ),
    path(
        "variants/samplesReceivedOverTimePie",
        views.samples_received_over_time_pie,
        name="samples_received_over_time_pie",
    ),
    path(
        "variants/samplesReceivedOverTimePieLaboratory",
        views.samples_received_over_time_pie_laboratory,
        name="samples_received_over_time_pie_laboratory",
    ),
    path(
        "variants/spikeMutations3DColor",
        views.spike_mutations_3D_color,
        name="spike_mutations_3D_color",
    ),
    path(
        "variants/spikeMutations3DBN",
        views.spike_mutations_3D_BN,
        name="spike_mutations_3D_BN",
    ),
    path("Gauge", views.gauge_test, name="gauge"),
    # Methodology graphics
    path("methodology", views.methodology_index, name="methodology_index"),
    path(
        "methodology/fields_utilization",
        views.methodology_fields_utilization,
        name="methodology_fields_utilization",
    ),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
