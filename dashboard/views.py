# Generic imports
from django.shortcuts import render

# Local imports
import core.utils.lineage
import core.utils.variants
import dashboard.dashboard_config
import dashboard.utils.met_bioinfo
import dashboard.utils.met_host_info
import dashboard.utils.met_index
import dashboard.utils.met_sample_preprocessing
import dashboard.utils.met_sequencing
import dashboard.utils.plotly
import dashboard.utils.var_lineage_variation_over_time_graph
import dashboard.utils.var_needle_mutation_graph_by_lineage


def variants_index(request):
    return render(request, "dashboard/variantsIndex.html")


def mutations_in_lineage(request):
    # mutations in lineages by lineage
    def_chrom = core.utils.variants.get_default_chromosome()
    lineages_list = core.utils.lineage.get_lineages_list()
    mdata, lineage, n_samples = (
        dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages(
            graphic_name="variations_per_lineage", lineage=None, chromosome=def_chrom
        )
    )

    if not mdata:
        return render(
            request,
            "dashboard/variantMutationsInLineage.html",
            {"ERROR": dashboard.dashboard_config.ERROR_NO_LINEAGES_ARE_DEFINED_YET},
        )
    initial_arguments = dashboard.utils.var_needle_mutation_graph_by_lineage.create_needle_plot_graph_mutation_by_lineage(
        lineages_list, lineage, mdata, n_samples
    )
    if "ERROR" in initial_arguments:
        return render(
            request,
            "dashboard/variantMutationsInLineage.html",
            {"ERROR": initial_arguments["ERROR"]},
        )
    return render(
        request,
        "dashboard/variantMutationsInLineage.html",
        {"needle_plot_initial_arguments": initial_arguments},
    )


def lineages_voc(request):
    # Draw lineage based on time
    draw_lineages = {}
    draw_lineages["lineage_on_time"] = (
        dashboard.utils.var_lineage_variation_over_time_graph.create_lineages_variations_graphic()
    )
    return render(
        request,
        "dashboard/variantLineageVoc.html",
        {"draw_lineages": draw_lineages},
    )


def methodology_index(request):
    graphics = dashboard.utils.met_index.index_dash_fields()
    return render(request, "dashboard/methodologyIndex.html", {"graphics": graphics})


def methodology_host_info(request):
    host_info = dashboard.utils.met_host_info.host_info_graphics()
    if "ERROR" in host_info:
        return render(
            request, "dashboard/methodologyHostInfo.html", {"ERROR": host_info}
        )
    return render(
        request, "dashboard/methodologyHostInfo.html", {"host_info": host_info}
    )


def methodology_sequencing(request):
    sequencing = dashboard.utils.met_sequencing.sequencing_graphics()
    if "ERROR" in sequencing:
        return render(
            request,
            "dashboard/methodologySequencing.html",
            {"ERROR": sequencing},
        )
    return render(
        request,
        "dashboard/methodologySequencing.html",
        {"sequencing": sequencing},
    )


def methodology_sample_processing(request):
    sample_processing = (
        dashboard.utils.met_sample_preprocessing.sample_processing_graphics()
    )
    if "ERROR" in sample_processing:
        return render(
            request,
            "dashboard/methodologySampleProcessing.html",
            {"ERROR": sample_processing},
        )
    return render(
        request,
        "dashboard/methodologySampleProcessing.html",
        {"sample_processing": sample_processing},
    )


def methodology_bioinfo(request):
    bioinfo = dashboard.utils.met_bioinfo.bioinfo_graphics()
    return render(request, "dashboard/methodologyBioinfo.html", {"bioinfo": bioinfo})
