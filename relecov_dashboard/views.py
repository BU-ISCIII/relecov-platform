from django.shortcuts import render
from relecov_dashboard.utils.graphics.variant_mutation_in_lineages_search_by_lineage import (
    create_needle_plot_graph_ITER,
)

from relecov_dashboard.utils.graphics.molecule3D_graph import (
    create_molecule3D_zoom_specific_residues,
)
from relecov_dashboard.utils.graphics.variant_mutations_in_lineages_search_by_sample import (
    create_needle_plot_graph,
)
from relecov_dashboard.utils.graphics.mutations_3D_molecule import create_graph
from relecov_dashboard.utils.graphics.mutation_table import create_mutation_table

from relecov_dashboard.utils.graphics.mutation_heatmap import create_hot_map

from relecov_dashboard.utils.graphics.geo_json import create_json

from relecov_dashboard.utils.graphics.samples_per_ccaa_geojson import query_to_database
from relecov_dashboard.utils.methodology_index import index_dash_fields

from relecov_core.utils.handling_variant import (
    create_dataframe,
    get_variant_data_from_lineages,
)


def variants_index(request):
    return render(request, "relecov_dashboard/variantsIndex.html")


def methodology_index(request):
    index_dash_fields()
    return render(request, "relecov_dashboard/methodologyIndex.html")


def lineages(request):
    # include lineages_variation_over_time.html(Alejandro Sanz from Fisabio)
    create_json("BA.1.1.1")
    return render(request, "relecov_dashboard/dashboard_templates/lineages.html")


def variants_lineage_variation_over_time(request):
    # waiting for the missing input file
    # make_lineage_variaton_plot()
    return render(request, "relecov_dashboard/variantsLineageVariationOverTime.html")


def variants_mutations_in_lineages_heatmap(request):
    create_hot_map(2018185)
    return render(request, "relecov_dashboard/variantsMutationsInLineagesHeatmap.html")


def mutations_in_lineages_by_lineage(request):
    mdata = get_variant_data_from_lineages("B.1.1.7", "NC_045512")
    create_needle_plot_graph_ITER("BA.1.1.7", mdata)
    # create_lineage_in_time_graph()
    # create_needle_plot_graph(sample=None)
    # create_mutation_table(214821)
    # create_hot_map()
    return render(request, "relecov_dashboard/variants_lineages_voc.html")


def mutations_in_lineages_by_samples(request):
    mdata = create_dataframe(sample=2018185, organism_code="NC_045512")
    create_needle_plot_graph(sample=None, mdata=mdata)
    return render(
        request, "relecov_dashboard/variantsMutationsInLineagesNeedlePlot.html"
    )


def variants_mutations_in_lineages_table(request):
    create_mutation_table(2018185)
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
    return render(request, "relecov_dashboard/methodologytest2.html")
