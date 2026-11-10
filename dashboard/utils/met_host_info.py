# Generic imports
import pandas as pd

# Local imports
import dashboard.dashboard_config
import dashboard.utils.generic_process_data
import dashboard.utils.plotly
import dashboard.utils.generic_graphic_data


def host_info_graphics():
    host_info_json = dashboard.utils.generic_graphic_data.get_graphic_json_data(
        "host_info"
    )
    if host_info_json is None:
        dashboard.utils.generic_process_data.pre_proc_host_info()
        host_info_json = dashboard.utils.generic_graphic_data.get_graphic_json_data(
            "host_info"
        )

    host_info_plots = {}
    host_info_plots["gender_graph"] = dashboard.utils.plotly.pie_graphic(
        labels=host_info_json["gender_label"],
        values=host_info_json["gender_values"],
        options={"title": "Gender distribution"},
    )
    host_gender_age_df = pd.DataFrame(
        host_info_json["gender_data"],
        columns=["range_age", "Male", "Female", "Not Provided"],
    )
    col_names = list(host_gender_age_df.columns)
    host_info_plots["gender_age_graph"] = dashboard.utils.plotly.bar_graphic(
        data=host_gender_age_df,
        col_names=col_names,
        legend=col_names[1:],
        yaxis={"title": "Number of samples"},
        options={
            "title": "Sample Distribution by Host Age and Gender",
            "height": 300,
        },
    )
    host_age_df = pd.DataFrame(
        host_info_json["host_age_data"].items(), columns=["range_age", "number"]
    )
    host_info_plots["range_age_graph"] = dashboard.utils.plotly.bar_graphic(
        data=host_age_df,
        col_names=["range_age", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "Sample Distribution by Host Age", "height": 300},
    )
    if any(v > 0 for v in host_info_json["invalid_data"].values()):
        total_invalid_data = sum(x for x in host_info_json["invalid_data"].values())
        host_info_plots["invalid_data"] = total_invalid_data
    return host_info_plots
