from relecov_dashboard.utils.plotly_graphics import bar_graphic
from relecov_core.utils.rest_api_handling import get_stats_data
import pdb
import pandas as pd


def host_info_graphics():
    def fetching_data_for_host_info():

        # get stats utilization fields from LIMS
        lims_fields = get_stats_data(
            {"sample_project_name": "Relecov", "project_field": "host_age"}
        )
        # order data by age
        host_age = {}
        # ages = list(lims_fields.keys())

        for key, val in lims_fields.items():
            try:
                host_age[int(key)] = val
            except ValueError:
                continue
        pdb.set_trace()
        host_age_df = pd.DataFrame(host_age.items(), columns=["age", "number"])
        host_age_df = host_age_df.sort_values("age")
        return host_age_df

    # sort_age = list(ages_int.keys()).sort()
    host_info = {}
    host_age_df = fetching_data_for_host_info()
    host_info["range_age_graph"] = bar_graphic(
        data=host_age_df,
        col_names=["age", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Samples received for host age", "height": 300},
    )

    # pdb.set_trace()
    return host_info
