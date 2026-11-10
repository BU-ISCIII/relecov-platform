# Generic imports
from collections import OrderedDict
from statistics import mean

# Local imports
import logging
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
        json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
            "bioinfo_percentage_data"
        )
        if json_data is None or json_data == {}:
            result = (
                dashboard.utils.generic_process_data.pre_proc_bioinfo_percentage_data()
            )
            if "ERROR" in result:
                return result
            json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
                "bioinfo_percentage_data"
            )

        per_data = []
        for label, values in json_data.items():
            if not isinstance(values, (list, tuple)):
                logger.warning(
                    f"Skipping bioinfo percentage series '{label}' because it is not a list"
                )
                continue
            per_data.append({label: list(values)})
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
