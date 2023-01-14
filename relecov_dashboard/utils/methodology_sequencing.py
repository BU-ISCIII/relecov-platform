import pandas as pd
from statistics import mean
from relecov_dashboard.utils.plotly_graphics import (
    bar_graphic,
    box_plot_graphic,
    line_graphic,
)
from relecov_core.utils.rest_api_handling import get_stats_data
from relecov_dashboard.utils.generic_functions import get_graphic_json_data
from relecov_dashboard.utils.pre_processing_data import (
    pre_proc_library_kit_pcr_1,
    pre_proc_based_pairs_sequenced,
)


def sequencing_graphics():
    def get_pre_proc_data(graphic_name, out_format):
        """Get the pre-processed data for the graphic name.
        If there is not data stored for the graphic, it will query to store
        them before calling for the second time
        """
        json_data = get_graphic_json_data(graphic_name)
        if json_data is None:
            # Execute the pre-processed task to get the data
            if graphic_name == "library_kit_pcr_1":
                result = pre_proc_library_kit_pcr_1()
            elif graphic_name == "ct_number_of_base_pairs_sequenced":
                result = pre_proc_based_pairs_sequenced()
            else:
                return {"ERROR": "pre-processing not defined"}
            if "ERROR" in result:
                return result
        json_data = get_graphic_json_data(graphic_name)
        if out_format == "list_of_dict":
            data = []
            for key, values in json_data.items():
                # Convert string to float values
                tmp_data = []
                for str_val, numbers in values.items():
                    try:
                        float_val = float(str_val)
                    except ValueError:
                        continue
                    tmp_data += [float_val] * numbers
                data.append({key: tmp_data})
        else:
            data = {"based": [], "cts": []}
            for key, values in json_data.items():
                data["based"].append(int(key))
                data["cts"].append(mean(values))
        return data

    def fetching_data_for_sequencing_data(project_field, columns):

        # get stats utilization fields from LIMS
        lims_data = get_stats_data(
            {
                "sample_project_name": "Relecov",
                "project_field": project_field,
            }
        )
        if "ERROR" in lims_data:
            return lims_data
        return pd.DataFrame(lims_data.items(), columns=columns)

    sequencing = {}
    inst_platform_df = fetching_data_for_sequencing_data(
        project_field="sequencing_instrument_platform",
        columns=["instrument_platform", "number"],
    )
    if "ERROR" in inst_platform_df:
        return inst_platform_df
    sequencing["instrument_platform"] = bar_graphic(
        data=inst_platform_df,
        col_names=["instrument_platform", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Instrument platform", "height": 400},
    )
    inst_model_df = fetching_data_for_sequencing_data(
        project_field="sequencing_instrument_model",
        columns=["instrument_model", "number"],
    )
    sequencing["instrument_model"] = bar_graphic(
        data=inst_model_df,
        col_names=["instrument_model", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Instrument model", "height": 400},
    )
    lib_preparation_df = fetching_data_for_sequencing_data(
        project_field="library_preparation_kit",
        columns=["library_preparation", "number"],
    )
    sequencing["library_preparation"] = bar_graphic(
        data=lib_preparation_df,
        col_names=["library_preparation", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Library preparation", "height": 400},
    )
    read_length_df = fetching_data_for_sequencing_data(
        project_field="read_length",
        columns=["read_length", "number"],
    )
    sequencing["read_length"] = bar_graphic(
        data=read_length_df,
        col_names=["read_length", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Read length", "height": 400, "colors": "#1aff8c"},
    )
    # box plot for library preparation kit

    cts_library_data = get_pre_proc_data("library_kit_pcr_1", "list_of_dict")
    sequencing["cts_library"] = box_plot_graphic(
        cts_library_data,
        {"title": "Boxplot Cts / Library preparation kit", "height": 400, "width": 420},
    )

    cts_pcr_1 = get_pre_proc_data("ct_number_of_base_pairs_sequenced", "dict")
    sequencing["number_of_base"] = line_graphic(
        cts_pcr_1["based"],
        cts_pcr_1["cts"],
        {
            "title": "Number of base",
            "height": 350,
            "width": 300,
            "x_title": "Number of base pairs",
            "y_title": "PCR CT 1",
        },
    )
    return sequencing
