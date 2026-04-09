# Generic imports
from statistics import mean
import pandas as pd
import logging

# Local imports
import core.utils.rest_api
import dashboard.utils.generic_graphic_data
import dashboard.utils.plotly
import dashboard.utils.generic_process_data

logger = logging.getLogger(__name__)


def sequencing_graphics():
    def get_pre_proc_data(graphic_name, out_format):
        """Get the pre-processed data for the graphic name.
        If there is not data stored for the graphic, it will query to store
        them before calling for the second time
        """
        json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
            graphic_name
        )
        if json_data is None or json_data == {}:
            # Execute the pre-processed task to get the data
            if graphic_name == "library_kit_pcr_1":
                result = (
                    dashboard.utils.generic_process_data.pre_proc_library_kit_pcr_1()
                )
            elif graphic_name == "ct_number_of_base_pairs_sequenced":
                result = (
                    dashboard.utils.generic_process_data.pre_proc_based_pairs_sequenced()
                )
            else:
                return {"ERROR": "pre-processing not defined"}
            if "ERROR" in result:
                return result
            json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
                graphic_name
            )
        if out_format == "list_of_dict":
            data = []
            for key, values in json_data.items():
                # Convert string to float values
                tmp_data = []
                for str_val, numbers in values.items():
                    try:
                        float_val = float(str_val)
                    except ValueError:
                        try:
                            float_val = float(str(str_val).replace(",", "."))
                        except Exception:
                            logger.warning(
                                f"Non-numeric CT value '{str_val}' found in bin '{key}' - skipping."
                            )
                            continue
                    if float_val > 40:
                        logger.info(
                            f"Discarded CT value > 40: {float_val} in bin '{key}'"
                        )
                        continue
                    tmp_data += [float_val] * numbers
                data.append({key: tmp_data})
        else:
            data = {"based": [], "cts": []}
            for key, values in json_data.items():
                try:
                    int_key = int(key)
                except ValueError:
                    logger.warning(f"Invalid bin key '{key}' - skipping.")
                    continue

                filtered_vals = [
                    v for v in values if isinstance(v, (int, float)) and v <= 40
                ]
                discarded = len(values) - len(filtered_vals)

                if discarded > 0:
                    logger.info(f"{discarded} CT values > 40 discarded in bin {key}")

                if not filtered_vals:
                    logger.debug(f"All values discarded for bin {key} - skipping.")
                    continue

                data["based"].append(int_key)
                data["cts"].append(mean(filtered_vals))
        return data

    def fetch_sequencing_data(project_field, columns):
        json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
            project_field
        )
        if json_data is None or json_data == {}:
            pre_proc_methods = {
                "sequencing_instrument_platform": (
                    dashboard.utils.generic_process_data.pre_proc_sequencing_instrument_platform
                ),
                "sequencing_instrument_model": (
                    dashboard.utils.generic_process_data.pre_proc_sequencing_instrument_model
                ),
                "library_preparation_kit": (
                    dashboard.utils.generic_process_data.pre_proc_library_preparation_kit
                ),
                "read_length": dashboard.utils.generic_process_data.pre_proc_read_length,
            }
            pre_proc_method = pre_proc_methods.get(project_field)
            if pre_proc_method is None:
                return {"ERROR": "pre-processing not defined"}
            result = pre_proc_method()
            if "ERROR" in result:
                return result
            json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
                project_field
            )
        return pd.DataFrame(json_data.items(), columns=columns)

    sequencing = {}
    inst_platform_df = fetch_sequencing_data(
        project_field="sequencing_instrument_platform",
        columns=["instrument_platform", "number"],
    )
    if "ERROR" in inst_platform_df:
        return inst_platform_df
    sequencing["instrument_platform"] = dashboard.utils.plotly.bar_graphic(
        data=inst_platform_df,
        col_names=["instrument_platform", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Instrument Platform", "height": 400},
    )
    inst_model_df = fetch_sequencing_data(
        project_field="sequencing_instrument_model",
        columns=["instrument_model", "number"],
    )
    sequencing["instrument_model"] = dashboard.utils.plotly.bar_graphic(
        data=inst_model_df,
        col_names=["instrument_model", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Instrument Model", "height": 400},
    )
    lib_preparation_df = fetch_sequencing_data(
        project_field="library_preparation_kit",
        columns=["library_preparation", "number"],
    )
    lib_preparation_df["library_preparation"] = (
        lib_preparation_df["library_preparation"]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace({"": "Not Applicable"})
    )
    sequencing["library_preparation"] = dashboard.utils.plotly.bar_graphic(
        data=lib_preparation_df,
        col_names=["library_preparation", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Library Preparation", "height": 400, "truncate_labels": 20},
    )
    read_length_df = fetch_sequencing_data(
        project_field="read_length",
        columns=["read_length", "number"],
    )

    read_length_df["read_length"] = pd.to_numeric(
        read_length_df["read_length"], errors="coerce"
    )
    read_length_df = read_length_df.dropna()
    read_length_df = read_length_df.groupby("read_length", as_index=False)[
        "number"
    ].sum()

    sequencing["read_length"] = dashboard.utils.plotly.bar_graphic(
        data=read_length_df,
        col_names=["read_length", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={
            "title": "Read Length Distribution",
            "height": 400,
            "width": 400,
            "xaxis": {"type": "category"},
            "log_scaling": True,
        },
    )
    # box plot for library preparation kit

    cts_library_data = get_pre_proc_data("library_kit_pcr_1", "list_of_dict")
    sequencing["cts_library"] = dashboard.utils.plotly.box_plot_graphic(
        cts_library_data,
        {
            "title": "PCR Ct Values by Library Preparation Kit",
            "height": 400,
            "width": 350,
            "y_title": "PCR Ct Value",
            "truncate_labels": 20,
        },
    )

    cts_pcr_1 = get_pre_proc_data("ct_number_of_base_pairs_sequenced", "dict")
    sequencing["number_of_base"] = dashboard.utils.plotly.line_graphic(
        cts_pcr_1["based"],
        cts_pcr_1["cts"],
        {
            "title": "Sequenced Base Pairs vs PCR Ct Values",
            "height": 350,
            "width": 300,
            "x_title": "Number of base pairs sequenced",
            "y_title": "PCR Ct Value",
        },
    )
    return sequencing
