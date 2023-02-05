import pandas as pd
from collections import OrderedDict
from relecov_dashboard.utils.graphics.plotly_graphics import bar_graphic, pie_graphic
from relecov_core.utils.rest_api_handling import get_stats_data

from relecov_dashboard.dashboard_config import HOST_RANGE_AGE_TEXT


def host_info_graphics():
    def split_age_in_ranges(data):
        tmp_range = {}
        invalid_data = 0
        for key, val in data.items():
            try:
                int_key = int(key)
            except ValueError:
                continue
            quotient = int_key // 10
            if quotient < 0:
                invalid_data += val
                continue
            if quotient not in tmp_range:
                tmp_range[quotient] = 0
            tmp_range[quotient] += val
        return tmp_range, invalid_data

    def fetching_data_for_range_age():

        # get stats utilization fields from LIMS
        lims_fields = get_stats_data(
            {"sample_project_name": "Relecov", "project_field": "host_age"}
        )
        host_age = {}
        for key, val in lims_fields.items():
            try:
                host_age[int(key)] = val
            except ValueError:
                continue
        # group data by decimal range

        tmp_range, invalid_data = split_age_in_ranges(lims_fields)
        max_value = max(tmp_range.keys())
        host_age_range = OrderedDict()
        for idx in range(max_value + 1):
            try:
                host_age_range[HOST_RANGE_AGE_TEXT[idx]] = tmp_range[idx]
            except KeyError:
                host_age_range[HOST_RANGE_AGE_TEXT[idx]] = 0
        host_age_range_df = pd.DataFrame(
            host_age_range.items(), columns=["range_age", "number"]
        )
        return host_age_range_df, invalid_data

    def fetching_data_for_sex_and_range_data():
        lims_fields = get_stats_data(
            {"sample_project_name": "Relecov", "project_field": "host_gender,host_age"}
        )
        max_value = 0
        invalid_data = 0
        tmp_range_per_key = {}
        host_age_range_per_key_df = pd.DataFrame()
        for key, values in lims_fields.items():
            tmp_range_per_key[key], tmp_invalid_data = split_age_in_ranges(values)
            invalid_data += tmp_invalid_data
            tmp_max_value = max(tmp_range_per_key[key].keys())
            if tmp_max_value > max_value:
                max_value = tmp_max_value

        age_range_list = []
        for idx in range(max_value + 1):
            age_range_list.append(HOST_RANGE_AGE_TEXT[idx])
        host_age_range_per_key_df["range_age"] = age_range_list

        for key in tmp_range_per_key.keys():
            age_range_list = []
            for idx in range(max_value + 1):
                try:
                    age_range_list.append(tmp_range_per_key[key][idx])
                except KeyError:
                    age_range_list.append(0)
            host_age_range_per_key_df[key] = age_range_list

        return host_age_range_per_key_df, invalid_data

    def fetching_data_for_gender():
        # get stats for host gender from LIMS
        lims_fields = get_stats_data(
            {"sample_project_name": "Relecov", "project_field": "host_gender"}
        )
        if "ERROR" in lims_fields:
            return lims_fields, ""
        labels = []
        values = []
        for key, val in lims_fields.items():
            labels.append(key)
            values.append(val)
        return labels, values

    # sort_age = list(ages_int.keys()).sort()
    host_info = {}
    # pie graphic for gender
    gender_label, gender_values = fetching_data_for_gender()
    if "ERROR" in gender_label:
        return gender_label
    host_info["gender_graph"] = pie_graphic(
        labels=gender_label,
        values=gender_values,
        options={"title": "Gender distribution"},
    )
    # graphic for gender and age
    host_gender_age_df = fetching_data_for_sex_and_range_data()[0]
    col_names = list(host_gender_age_df.columns)
    host_info["gender_age_graph"] = bar_graphic(
        data=host_gender_age_df,
        col_names=col_names,
        legend=col_names[1:],
        yaxis={"title": "Number of samples"},
        options={
            "title": "Samples received for host gender and host age",
            "height": 300,
        },
    )
    host_age_df, invalid_data = fetching_data_for_range_age()
    host_info["range_age_graph"] = bar_graphic(
        data=host_age_df,
        col_names=["range_age", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Samples received for host age", "height": 300},
    )
    if invalid_data > 0:
        host_info["invalid_data"] = invalid_data
    return host_info
