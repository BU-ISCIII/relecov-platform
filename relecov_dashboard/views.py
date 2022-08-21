from django.shortcuts import render
from relecov_dashboard.utils.graphics.iter_plot import create_needle_plot_graph_ITER

"""
from relecov_dashboard.utils.graphics.lineages_in_time_graph import (
    create_lineage_in_time_graph,
)
"""
from relecov_dashboard.utils.graphics.molecule3D_graph import (
    create_molecule3D_zoom_specific_residues,
)
from relecov_dashboard.utils.graphics.needle_plot_graph import create_needle_plot_graph
from relecov_dashboard.utils.graphics.mutations_3D_molecule import create_graph
from relecov_dashboard.utils.graphics.mutation_table import create_mutation_table

# from relecov_dashboard.utils.graphics.lineage_by_CCAA_geomap_graph import plot_geomap
from relecov_dashboard.utils.graphics.mutation_heatmap import create_hot_map

from relecov_dashboard.utils.graphics.geo_json import create_json

# from relecov_dashboard.utils.graphics.gauge import create_gauge, create_medium_gauge
from relecov_dashboard.utils.graphics.samples_per_ccaa_geojson import query_to_database

#
from relecov_dashboard.utils.methodology_fields import schema_fields_utilization


def variants_index(request):
    return render(request, "relecov_dashboard/variantsIndex.html")


def methodology_index(request):
    return render(request, "relecov_dashboard/methodologyIndex.html")


def variants_lineages_voc(request):
    create_needle_plot_graph_ITER("BA.1.1.1")
    # create_lineage_in_time_graph()
    # create_needle_plot_graph(sample=None)
    # create_mutation_table(214821)
    # create_hot_map()
    return render(request, "relecov_dashboard/variants_lineages_voc.html")


def lineages(request):
    # include lineages_variation_over_time.html(Alejandro Sanz from Fisabio)
    create_json("BA.1.1.1")
    return render(request, "relecov_dashboard/dashboard_templates/lineages.html")


def variants_lineage_variation_over_time(request):
    # waiting for the missing input file
    # make_lineage_variaton_plot()
    return render(request, "relecov_dashboard/variantsLineageVariationOverTime.html")


def variants_mutations_in_lineages_heatmap(request):
    create_hot_map()
    return render(request, "relecov_dashboard/variantsMutationsInLineagesHeatmap.html")


def variants_mutations_in_lineages_needle_plot(request):
    create_needle_plot_graph(sample=None)
    return render(
        request, "relecov_dashboard/variantsMutationsInLineagesNeedlePlot.html"
    )


def variants_mutations_in_lineages_table(request):
    create_mutation_table(214821)
    return render(request, "relecov_dashboard/variantsMutationsInLineagesTable.html")


def spike_mutations(request):
    create_molecule3D_zoom_specific_residues()
    create_graph()
    return render(request, "relecov_dashboard/dashboard_templates/spike_mutations.html")


def gauge_test(request):
    # create_gauge()
    # create_medium_gauge()
    query_to_database()
    return render(request, "relecov_dashboard/dashboard_templates/gauge2.html")
    # return render(request, "relecov_dashboard/dashboard_templates/gauge.html")


def methodology_fields_utilization(request):
    f_utilization = schema_fields_utilization()
    return render(
        request,
        "relecov_dashboard/dashboard_templates/methodologyFieldsUtilization.html",
        {"f_utilization": f_utilization},
    )
