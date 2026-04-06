# Generic imports
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Local imports
import core.config
import core.utils.lineage
import core.utils.variants
import dashboard.dashboard_config
import dashboard.utils.met_bioinfo
import dashboard.utils.met_host_info
import dashboard.utils.met_index
import dashboard.utils.met_sample_preprocessing
import dashboard.utils.met_sequencing
import dashboard.utils.plotly
import dashboard.utils.var_heatmap_mutation_graph_by_lineage
import dashboard.utils.var_lineage_variation_over_time_graph
import dashboard.utils.var_lineages_in_time
import dashboard.utils.var_molecule3D_bn_graph
import dashboard.utils.var_needle_mutation_graph_by_lineage
import dashboard.utils.var_samples_received_over_time_pie


# dashboard/variants
@login_required
def variants_index(request):
    return render(request, "dashboard/variantsIndex.html")


@login_required
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


# FIXME: template html has bad ref in plotly_app. App name shoudl be replaced by 'model3D_bn'
# FIXME: Couldn't find in variants dashboard a button or ref to acces this url
@login_required
def spike_mutations_3d(request):
    dashboard.utils.var_molecule3D_bn_graph.create_model3D_bn()
    return render(request, "dashboard/variantSpikeMutations3D.html")


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


# FIXME: isn't called from urls.py and html template is not available.
@login_required
def samples_received_over_time_graph(request):
    df = dashboard.utils.var_lineages_in_time.create_dataframe_from_json()
    dashboard.utils.var_lineages_in_time.create_samples_over_time_graph(df)

    return render(request, "dashboard/samplesReceivedOverTimeGraph.html")


# FIXME: isn't called from urls.py and html template is not available.
@login_required
def samples_received_over_time_pie(request):
    data = dashboard.utils.var_samples_received_over_time_pie.parse_json_file()
    dashboard.utils.var_samples_received_over_time_pie.create_samples_received_over_time_per_ccaa_pieChart(
        data
    )
    dashboard.utils.var_samples_received_over_time_pie.create_samples_received_over_time_per_laboratory_pieChart(
        data
    )

    return render(request, "dashboard/samplesReceivedOverTimePie.html")


# FIXME: isn't called from urls.py and html template is not available.
@login_required
def samples_received_over_time_pie_laboratory(request):
    data = dashboard.utils.var_samples_received_over_time_pie.parse_json_file()
    dashboard.utils.var_samples_received_over_time_pie.create_samples_received_over_time_per_ccaa_pieChart(
        data
    )
    dashboard.utils.var_samples_received_over_time_pie.create_samples_received_over_time_per_laboratory_pieChart(
        data
    )

    return render(request, "dashboard/samplesReceivedOverTimePieLaboratory.html")


# FIXME: isn't called from urls.py and html template is not available.
@login_required
def variants_mutations_in_lineages_heatmap(request):
    chromesome_objs = core.utils.variants.get_all_chromosome_objs()
    if chromesome_objs is None:
        return render(
            request,
            "dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ERROR": core.config.ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE},
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
            "dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ORGANISM": chromesome_list},
        )
    gene_list = core.utils.variants.get_gene_list(chromesome_objs[0])
    if len(gene_list) == 0:
        return render(
            request,
            "dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ERROR": core.config.ERROR_GENE_NOT_DEFINED_IN_DATABASE},
        )
    sample_list = core.utils.variants.get_sample_in_variant_list(chromesome_objs[0])
    if len(sample_list) == 0:
        return render(
            request,
            "dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ERROR": core.config.ERROR_VARIANT_IN_SAMPLE_NOT_DEFINED},
        )
    return render(request, "dashboard/variantsMutationsInLineagesHeatmap.html")


# dashboard/methodology
@login_required
def methodology_index(request):
    graphics = dashboard.utils.met_index.index_dash_fields()
    return render(request, "dashboard/methodologyIndex.html", {"graphics": graphics})


@login_required
def methodology_host_info(request):
    host_info = dashboard.utils.met_host_info.host_info_graphics()
    if "ERROR" in host_info:
        return render(
            request, "dashboard/methodologyHostInfo.html", {"ERROR": host_info}
        )
    return render(
        request, "dashboard/methodologyHostInfo.html", {"host_info": host_info}
    )


@login_required
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


@login_required
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


@login_required
def methodology_bioinfo(request):
    bioinfo = dashboard.utils.met_bioinfo.bioinfo_graphics()
    return render(request, "dashboard/methodologyBioinfo.html", {"bioinfo": bioinfo})
