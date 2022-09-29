from django.shortcuts import render
from relecov_dashboard.utils.graphics.variant_mutation_in_lineages_search_by_lineage import (
    create_needle_plot_graph_mutation_by_lineage,
)

from relecov_dashboard.utils.graphics.molecule3D_graph import (
    create_molecule3D_zoom_specific_residues,
)
from relecov_dashboard.utils.graphics.variant_mutations_in_lineages_search_by_sample import (
    create_needle_plot_graph_mutation_by_sample,
)
from relecov_dashboard.utils.graphics.mutations_3D_molecule import create_graph
from relecov_dashboard.utils.graphics.mutation_table import create_mutation_table

from relecov_dashboard.utils.graphics.variant_mutation_in_lineages_heatmap import (
    create_heat_map,
)

from relecov_dashboard.utils.graphics.samples_received_over_time_map import (
    create_samples_received_over_time_map,
)

from relecov_dashboard.utils.graphics.samples_per_ccaa_geojson import query_to_database
from relecov_dashboard.utils.methodology_index import index_dash_fields

from relecov_core.utils.handling_variant import (
    create_dataframe,
    get_variant_data_from_lineages,
)

from relecov_dashboard.utils.graphics.lineages_in_time_graph import (
    # create_list_for_dataframe,
    # create_dataframe_variants_in_time,
    create_samples_over_time_graph,
    create_dataframe_from_json,
)


def variants_index(request):
    return render(request, "relecov_dashboard/variantsIndex.html")


def methodology_index(request):
    index_dash_fields()
    return render(request, "relecov_dashboard/methodologyIndex.html")


def samples_received_over_time_map(request):
    create_samples_received_over_time_map()
    return render(
        request, "relecov_dashboard/graph_templates/samplesReceivedOverTimeMap.html"
    )


def lineages(request):
    create_samples_received_over_time_map("BA.1.1.1")
    return render(request, "relecov_dashboard/dashboard_templates/lineages.html")


def samples_received_over_time_graph(request):
    df = create_dataframe_from_json()
    create_samples_over_time_graph(df)

    return render(request, "relecov_dashboard/samplesReceivedOverTimeGraph.html")


def variants_mutations_in_lineages_heatmap(request):
    gene_list = ["orf1ab", "ORF8", "S", "M", "N"]
    sample_list = [2018185, 210067]
    create_heat_map(sample_list, gene_list)
    return render(request, "relecov_dashboard/variantsMutationsInLineagesHeatmap.html")


def mutations_in_lineages_by_lineage(request):
    # sample_list = [2018185, 210067]
    mdata = get_variant_data_from_lineages(lineage="B.1.1.7", organism_code="NC_045512")
    create_needle_plot_graph_mutation_by_lineage("BA.1.1.7", mdata)
    return render(
        request, "relecov_dashboard/variantsMutationsInLineagesByLineage.html"
    )


def mutations_in_lineages_by_samples(request):
    mdata = create_dataframe(sample_name=2018185, organism_code="NC_045512")
    create_needle_plot_graph_mutation_by_sample(sample_name=2018185, mdata=mdata)
    return render(request, "relecov_dashboard/variantsMutationsInLineagesBySample.html")


def variants_mutations_in_lineages_table(request):
    sample_list = [2018185, 210067]
    effect_list = ["upstream_gene_variant", "synonymous_variant", "missense_variant"]
    create_mutation_table(sample_list, effect_list=effect_list)
    return render(request, "relecov_dashboard/variantsMutationsInLineagesTable.html")


def spike_mutations_3D_color(request):
    create_molecule3D_zoom_specific_residues()
    return render(
        request, "relecov_dashboard/dashboard_templates/spike_mutations_3D_Color.html"
    )


def spike_mutations_3D_BN(request):
    create_graph()
    return render(
        request, "relecov_dashboard/dashboard_templates/spike_mutations_3D_BN.html"
    )


def gauge_test(request):
    # create_gauge()
    # create_medium_gauge()
    query_to_database()
    return render(request, "relecov_dashboard/dashboard_templates/gauge2.html")
    # return render(request, "relecov_dashboard/dashboard_templates/gauge.html")


def methodology_fields_utilization(request):
    return render(request, "relecov_dashboard/methodologytest2.html")
