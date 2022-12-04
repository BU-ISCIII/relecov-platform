import pandas as pd

# from collections import OrderedDict
# from relecov_dashboard.utils.plotly_graphics import bar_graphic, pie_graphic
from relecov_core.utils.rest_api_handling import get_stats_data

# from relecov_dashboard.dashboard_config import HOST_RANGE_AGE_TEXT


def sequencing_graphics():
    def fetching_data_for_sequence_instrument():

        # get stats utilization fields from LIMS
        lims_fields = get_stats_data(
            {
                "sample_project_name": "Relecov",
                "project_field": "nucleic_acid_extraction_protocol",
            }
        )

        host_age_range_df = pd.DataFrame(
            lims_fields.items(), columns=["range_age", "number"]
        )
        return host_age_range_df
