import pandas as pd
from relecov_dashboard.utils.plotly_graphics import bar_graphic
from relecov_core.utils.rest_api_handling import get_stats_data


def sequencing_graphics():
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
    return sequencing
