from django.shortcuts import render

# import fucntions from core
from relecov_core.utils.handling_variant import (
    get_all_chromosome_objs,
    get_gene_list,
    get_sample_in_variant_list,
)

from relecov_core.core_config import (
    ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE,
    ERROR_GENE_NOT_DEFINED_IN_DATABASE,
    ERROR_VARIANT_IN_SAMPLE_NOT_DEFINED,
)
from relecov_dashboard.utils.graphics.variant_mutation_in_lineages_search_by_lineage import (
    create_needle_plot_graph_mutation_by_lineage,
)

from relecov_dashboard.utils.graphics.molecule3D_color_graph import (
    create_molecule3D_zoom_specific_residues,
)
from relecov_dashboard.utils.graphics.variant_mutations_in_lineages_search_by_sample import (
    create_needle_plot_graph_mutation_by_sample,
)
from relecov_dashboard.utils.graphics.molecule3D_bn_graph import create_model3D_bn
from relecov_dashboard.utils.graphics.variant_mutations_in_lineages_mutation_table import (
    create_mutation_table,
)

from relecov_dashboard.utils.graphics.variant_mutation_in_lineages_heatmap import (
    create_heat_map,
)

from relecov_dashboard.utils.graphics.samples_received_over_time_map import (
    create_samples_received_over_time_map,
)

# from relecov_dashboard.utils.graphics.samples_per_ccaa_geojson import query_to_database
from relecov_dashboard.utils.methodology_index import index_dash_fields

from relecov_core.utils.handling_variant import (
    create_dataframe,
    get_variant_data_from_lineages,
)

from relecov_dashboard.utils.graphics.samples_received_over_time_graph import (
    create_dataframe_from_json,
    create_samples_over_time_graph,
)


def variants_index(request):
    return render(request, "relecov_dashboard/variantsIndex.html")


def lineages_dashboard(request):
    # samples receive over time map
    create_samples_received_over_time_map()

    # samples receive over time graph
    df = create_dataframe_from_json()
    create_samples_over_time_graph(df)

    return render(
        request, "relecov_dashboard/dashboard_templates/lineagesDashboard.html"
    )


def mutations_in_lineages_dashboard(request):
    # mutations in lineages by sample
    mdata = create_dataframe(sample_name=2018185, organism_code="NC_045512")
    create_needle_plot_graph_mutation_by_sample(sample_name=2018185, mdata=mdata)

    # mutations in lineages by lineage
    mdata = get_variant_data_from_lineages(lineage="B.1.1.7", organism_code="NC_045512")
    create_needle_plot_graph_mutation_by_lineage("BA.1.1.7", mdata)

    # mutations in lineages heatmap
    gene_list = ["orf1ab", "ORF8", "S", "M", "N"]
    sample_list = [220880, 210067]
    create_heat_map(sample_list, gene_list)

    # mutations in lineages table format
    sample_list = [2018185, 210067]
    effect_list = ["upstream_gene_variant", "synonymous_variant", "missense_variant"]
    create_mutation_table(sample_list, effect_list=effect_list)

    return render(
        request,
        "relecov_dashboard/dashboard_templates/mutationsInLineagesDashboard.html",
    )


def spike_mutations_3d_dashboard(request):
    create_molecule3D_zoom_specific_residues()
    create_model3D_bn()
    return render(
        request, "relecov_dashboard/dashboard_templates/spikeMutations3dDashboard.html"
    )


def methodology_index(request):
    index_dash_fields()
    return render(request, "relecov_dashboard/methodologyIndex.html")


def samples_received_over_time_map(request):
    create_samples_received_over_time_map()
    return render(
        request, "relecov_dashboard/graph_templates/samplesReceivedOverTimeMap.html"
    )


def samples_received_over_time_graph(request):
    df = create_dataframe_from_json()
    create_samples_over_time_graph(df)

    return render(request, "relecov_dashboard/samplesReceivedOverTimeGraph.html")


def variants_mutations_in_lineages_heatmap(request):
    chromesome_objs = get_all_chromosome_objs()
    if chromesome_objs is None:
        return render(
            request,
            "relecov_dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ERROR": ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE},
        )
    if len(chromesome_objs) > 1:
        chromesome_list = []
        for chromesome_obj in chromesome_objs:
            chromesome_list.append(
                [
                    chromesome_objs.get_chromesome_id(),
                    chromesome_objs.get_chromesome_name(),
                ]
            )
        return render(
            request,
            "relecov_dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ORGANISM": chromesome_list},
        )
    gene_list = get_gene_list(chromesome_objs[0])
    if len(gene_list) == 0:
        return render(
            request,
            "relecov_dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ERROR": ERROR_GENE_NOT_DEFINED_IN_DATABASE},
        )
    sample_list = get_sample_in_variant_list(chromesome_objs[0])
    if len(sample_list) == 0:
        return render(
            request,
            "relecov_dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ERROR": ERROR_VARIANT_IN_SAMPLE_NOT_DEFINED},
        )
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
    create_model3D_bn()
    return render(
        request,
        "relecov_dashboard/dashboard_templates/spike_mutations_3D_BN.html",
    )


def gauge_test(request):
    # create_gauge()
    # create_medium_gauge()
    # query_to_database()
    return render(request, "relecov_dashboard/dashboard_templates/gauge2.html")
    # return render(request, "relecov_dashboard/dashboard_templates/gauge.html")


def methodology_fields_utilization(request):
    return render(request, "relecov_dashboard/methodologytest2.html")
