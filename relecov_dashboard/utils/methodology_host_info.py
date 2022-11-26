import pandas as pd
from collections import OrderedDict
from relecov_dashboard.utils.plotly_graphics import bar_graphic
from relecov_core.utils.rest_api_handling import get_stats_data
import pdb

from relecov_dashboard.dashboard_config import HOST_RANGE_AGE_TEXT


def host_info_graphics():
    def fetching_data_for_host_info_range_age():

        # get stats utilization fields from LIMS
        lims_fields = get_stats_data(
            {"sample_project_name": "Relecov", "project_field": "host_age"}
        )
        host_age = {}
        # range_list = HOST_RANGE_AGE_TEXT
        # ages = list(lims_fields.keys())

        for key, val in lims_fields.items():
            try:
                host_age[int(key)] = val
            except ValueError:
                continue
        # group data by decimal range
        tmp_range = {}
        invalid_data = 0
        for key, val in host_age.items():
            quotient = key // 10
            if quotient < 0:
                invalid_data += val
                continue 
            if quotient not in tmp_range:
                tmp_range[quotient] = 0
            tmp_range[quotient] += val
        max_value = max(tmp_range.keys())
        # host_age_range = OrderedDict(sorted(tmp_range.items()))
        host_age_range = OrderedDict()

        for idx in range(max_value):
            try:
                host_age_range[HOST_RANGE_AGE_TEXT[idx]] = tmp_range[idx]
            except KeyError:
                host_age_range[HOST_RANGE_AGE_TEXT[idx]] = 0
        
        host_age_range_df = pd.DataFrame(host_age_range.items(), columns=["range_age", "number"])
        # host_age_range_df = host_age_range_df.sort_values("range_age")
        return host_age_range_df , invalid_data

    # sort_age = list(ages_int.keys()).sort()
    host_info = {}
    host_age_df , invalid_data = fetching_data_for_host_info_range_age()
    host_info["range_age_graph"] = bar_graphic(
        data=host_age_df,
        col_names=["range_age", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Samples received for host age", "height": 300},
    )
    if invalid_data > 0:
        host_info["invalid_data"] = invalid_data
    # pdb.set_trace()
    return host_info
