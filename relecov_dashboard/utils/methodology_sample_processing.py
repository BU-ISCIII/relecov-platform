import pandas as pd
from relecov_core.utils.rest_api_handling import get_stats_data
from relecov_dashboard.utils.plotly_graphics import bar_graphic


def sample_processing_graphics():
    def fetching_data_for_nuleic_protocol():

        # get stats utilization fields from LIMS about nucleic acid extaction
        # protocol
        lims_data = get_stats_data(
            {
                "sample_project_name": "Relecov",
                "project_field": "nucleic_acid_extraction_protocol",
            }
        )
        if "ERROR" in lims_data:
            return lims_data
        extraction_protocol_df = pd.DataFrame(
            lims_data.items(), columns=["protocol", "number"]
        )
        return extraction_protocol_df

    sample_processing = {}
    extraction_protocol_df = fetching_data_for_nuleic_protocol()
    if "ERROR" in extraction_protocol_df:
        return extraction_protocol_df
    sample_processing["nucleic_protocol"] = bar_graphic(
        data=extraction_protocol_df,
        col_names=["protocol", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Nucleic acid extraction protocol", "height": 400},
    )
    return sample_processing
