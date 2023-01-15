from statistics import mean
from collections import OrderedDict
from relecov_dashboard.utils.plotly_graphics import box_plot_graphic, line_graphic
from relecov_dashboard.utils.generic_functions import get_graphic_json_data
from relecov_core.models import BioinfoAnalysisValue
from relecov_dashboard.utils.pre_processing_data import pre_proc_depth_variants


def bioinfo_graphics():
    def get_pre_proc_data(graphic_name):
        json_data = get_graphic_json_data(graphic_name)
        if json_data is None:
            # Execute the pre-processed task to get the data
            if graphic_name == "depth_variant_consensus":
                result = pre_proc_depth_variants()
            elif graphic_name == "":
                pass
                # result = pre_proc_depth_sample_run()
            else:
                return {"ERROR": "pre-processing not defined"}
            if "ERROR" in result:
                return result
            json_data = get_graphic_json_data(graphic_name)
        tmp_json_float = {}
        for key, values in json_data.items():
            tmp_json_float[float(key)] = values
        json_data_sorted = OrderedDict(sorted(tmp_json_float.items()))
        data = {}
        data = {"depth": [], "variant": []}
        for key, values in json_data_sorted.items():
            data["depth"].append(float(key))
            data["variant"].append(mean(values))
        # import pdb; pdb.set_trace()
        return data

    def get_percentage_data():
        per_data = []
        graph_list = ["per_Ns", "per_reads_host", "per_reads_virus", "per_unmapped"]
        for graph in graph_list:
            if BioinfoAnalysisValue.objects.filter(
                bioinfo_analysis_fieldID__property_name__exact=graph
            ).exists():
                str_data = list(
                    BioinfoAnalysisValue.objects.filter(
                        bioinfo_analysis_fieldID__property_name__exact=graph
                    ).values_list("value", flat=True)
                )
                try:
                    per_data.append({graph: list(map(float, str_data))})
                except ValueError:
                    filter_list = []
                    for value in str_data:
                        try:

                            filter_list.append(float(value))
                        except ValueError:
                            continue
                    per_data.append({graph: filter_list})

        return per_data

    bioinfo = {}
    percentage_data = get_percentage_data()
    bioinfo["boxplot_comparation"] = box_plot_graphic(
        percentage_data,
        {"title": "Boxplot Percentage", "height": 400, "width": 420},
    )
    depth_variants_data = get_pre_proc_data("depth_variant_consensus")
    # import pdb; pdb.set_trace()
    bioinfo["depth_variants"] = line_graphic(
        depth_variants_data["depth"],
        depth_variants_data["variant"],
        {
            "title": "Depth / variant consensus",
            "height": 350,
            "width": 420,
            "x_title": "Depth",
            "y_title": "number of variants",
        },
    )
    #

    # get_pre_proc_data("depth_samples_in_run")
    return bioinfo
