from django.urls import path, include
from django.conf import settings

from relecov_dashboard import views
from django.conf.urls.static import static

urlpatterns = [
    path("variants", views.variants_index, name="variants_index"),
    path("django_plotly_dash/", include("django_plotly_dash.urls")),
    path(
        "methodology/fields_utilization",
        views.methodology_fields_utilization,
        name="methodology_fields_utilization",
    ),
    path(
        "variants/lineagesVoc",
        views.variants_lineages_voc,
        name="variants_lineages_voc",
    ),
    path("variants/lineages", views.lineages, name="lineages"),
    path(
        "variants/lineageVariationOverTime",
        views.variants_lineage_variation_over_time,
        name="variants_lineage_variation_over_time",
    ),
    path(
        "variants/mutationsInLineagesHeatmap",
        views.variants_mutations_in_lineages_heatmap,
        name="variants_mutations_in_lineages_heatmap",
    ),
    path(
        "variants/mutationsInLineagesNeedlePlot",
        views.variants_mutations_in_lineages_needle_plot,
        name="variants_mutations_in_lineages_needle_plot",
    ),
    path(
        "variants/mutationsInLineagesTable",
        views.variants_mutations_in_lineages_table,
        name="variants_mutations_in_lineages_table",
    ),
    path("spikeMutations", views.spike_mutations, name="spike_mutations"),
    path("Gauge", views.gauge_test, name="gauge"),
    # Methodology graphics
    path("methodology", views.methodology_index, name="methodology_index")
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
