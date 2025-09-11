# Generic imports
from collections import OrderedDict
from statistics import mean

# Local imports
import logging
import core.models
import dashboard.dashboard_config
import dashboard.utils.generic_graphic_data
import dashboard.utils.plotly
import dashboard.utils.generic_process_data

logger = logging.getLogger(__name__)


def bioinfo_graphics():
    def get_pre_proc_data(graphic_name):
        json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
            graphic_name
        )
        if json_data is None:
            # Execute the pre-processed task to get the data
            if graphic_name == "depth_variant_consensus":
                result = dashboard.utils.generic_process_data.pre_proc_depth_variants()
            elif graphic_name == "depth_samples_in_run":
                result = (
                    dashboard.utils.generic_process_data.pre_proc_depth_sample_run()
                )
            else:
                return {"ERROR": "pre-processing not defined"}
            if "ERROR" in result:
                return result
            json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
                graphic_name
            )

        tmp_json_float = {}
        for key, values in json_data.items():
            try:
                float_key = float(key)
                if not isinstance(values, (list, tuple)):
                    logger.warning(
                        f"Skipping key '{key}' because values are not a list or tuple: type={type(values).__name__}"
                    )
                    continue
                values_clean = [float(v) for v in values if isinstance(v, (int, float))]
                tmp_json_float[float_key] = values_clean
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping key '{key}' due to conversion error: {e}")
                continue

        json_data_sorted = OrderedDict(sorted(tmp_json_float.items()))
        data = {"depth": [], "variant": []}
        for key, values in json_data_sorted.items():
            if values:
                try:
                    data["depth"].append(float(key))
                    data["variant"].append(mean(values))
                except Exception as e:
                    logger.error(
                        f"Error processing key '{key}' with values '{values}': {e}"
                    )
                    print(f"[ERROR] Could not process key '{key}' due to: {e}")
                    continue
        return data

    def get_percentage_data():
        per_data = []
        graph_list = ["per_Ns", "per_reads_host", "per_reads_virus", "per_unmapped"]
        labels_map = {
            field.property_name: field.label_name
            for field in core.models.BioinfoAnalysisField.objects.filter(
                property_name__in=graph_list
            )
        }
        for graph in graph_list:
            if core.models.BioinfoAnalysisValue.objects.filter(
                bioinfo_analysis_fieldID__property_name__exact=graph
            ).exists():
                str_data = list(
                    core.models.BioinfoAnalysisValue.objects.filter(
                        bioinfo_analysis_fieldID__property_name__exact=graph
                    ).values_list("value", flat=True)
                )

                clean_values = []
                for value in str_data:
                    # Try direct float, then comma replacement
                    try:
                        v = float(value)
                    except (ValueError, TypeError):
                        try:
                            v = float(str(value).replace(",", "."))
                        except Exception:
                            logger.warning(
                                f"Invalid value encountered in '{graph}': '{value}' could not be converted to float"
                            )
                            continue
                    # Normalize and filter range
                    if v < 0:
                        v = 0.0
                    if v <= 100:
                        clean_values.append(v)

                per_data.append({labels_map.get(graph, graph): clean_values})

        return per_data

    bioinfo = {}
    percentage_data = get_percentage_data()
    if "ERROR" not in percentage_data:
        # Only render ridge plot if there is at least one data point
        try:
            total_points = sum(
                len(list(d.values())[0])
                for d in percentage_data
                if isinstance(d, dict) and d
            )
        except Exception:
            total_points = 0
        if total_points > 0:
            bioinfo["boxplot_comparation"] = dashboard.utils.plotly.ridge_plot_graphic(
                percentage_data,
                {"title": "Density Plot Percentage"},
            )
    depth_variants_data = get_pre_proc_data("depth_variant_consensus")
    if "ERROR" not in depth_variants_data:
        bioinfo["depth_variants"] = dashboard.utils.plotly.box_plot_graphic_bins(
            depth_variants_data["depth"],
            depth_variants_data["variant"],
            {
                "title": "Distribution of Variants Across Depth Ranges",
                "x_title": "Depth Range",
                "y_title": "number of variants",
            },
        )
    depth_sample_run_data = get_pre_proc_data("depth_samples_in_run")
    if "ERROR" not in depth_sample_run_data:
        bioinfo["depth_sample_run"] = dashboard.utils.plotly.box_plot_graphic_bins(
            depth_sample_run_data["depth"],
            depth_sample_run_data["variant"],
            {
                "title": "Number of Samples per Depth Interval",
                "x_title": "Depth Range",
                "y_title": "Samples in run",
            },
        )
    if not bioinfo:
        bioinfo["ERROR"] = dashboard.dashboard_config.ERROR_NOT_DATA_LOADED_YET
    return bioinfo
