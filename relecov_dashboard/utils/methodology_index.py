from statistics import mean

from relecov_core.utils.handling_bioinfo_analysis import (
    get_bioinfo_analyis_fields_utilization,
)
from relecov_core.utils.schema_handling import (
    get_default_schema,
)
from relecov_core.utils.rest_api_handling import get_stats_data
from relecov_dashboard.utils.graphics.plotly_graphics import bar_graphic,graph_gauge_percent_values


def schema_fields_utilization():
    """ """
    schema_obj = get_default_schema()
    if schema_obj is None:
        return

    util_data = {"summary": {}}
    util_data["summary"]["group"] = ["Empty Fields", "Total Fields"]
    util_data["field_detail_data"] = {"field_name": [], "field_value": []}

    # get stats utilization fields from LIMS
    lims_fields = get_stats_data({"sample_project_name": "Relecov"})
    if "ERROR" in lims_fields:
        util_data["ERROR"] = lims_fields["ERROR"]
    else:
        f_values = []
        for value in lims_fields["fields_norm"].values():
            f_values.append(value)
        if len(f_values) > 1:
            util_data["lims_f_values"] = float("%.1f" % (mean(f_values) * 100))
        else:
            util_data["lims_f_values"] = 0
        # Calculate empty fields and total fields
        empty_fields = len(lims_fields["always_none"]) + len(lims_fields["never_used"])
        total_fields = len(lims_fields["fields_norm"]) + empty_fields
        util_data["summary"]["lab_values"] = [empty_fields, total_fields]

        for key, val in lims_fields["fields_value"].items():
            util_data["field_detail_data"]["field_name"].append(key)
            util_data["field_detail_data"]["field_value"].append(val)
        util_data["num_lab_fields"] = len(lims_fields["fields_value"])

    # get fields utilization from bioinfo analysis
    bio_fields = get_bioinfo_analyis_fields_utilization(schema_obj)
    f_values = []
    for value in bio_fields["fields_norm"].values():
        f_values.append(value)
    if len(f_values) > 1:
        util_data["bio_f_values"] = float("%.1f" % (mean(f_values) * 100))
    else:
        util_data["bio_f_values"] = 0
    # Calculate empty fields and total fields for bio analysis fields
    empty_fields = len(bio_fields["always_none"]) + len(bio_fields["never_used"])
    total_fields = len(bio_fields["fields_norm"]) + empty_fields
    util_data["summary"]["bio_values"] = [empty_fields, total_fields]

    for key, val in bio_fields["fields_value"].items():
        util_data["field_detail_data"]["field_name"].append(key)
        util_data["field_detail_data"]["field_value"].append(val)
    util_data["num_bio_fields"] = len(bio_fields["fields_value"])

    return util_data


def index_dash_fields():
    graphics = {}
    util_data = schema_fields_utilization()
    graphics = {}
    if "ERROR" in util_data:
        graphics["ERROR"] = util_data["ERROR"]
        graphics["grouped_fields"] = bar_graphic(
            data=util_data["summary"],
            col_names=["group", "bio_values"],
            legend=["Bio analysis"],
            yaxis={"title": "Number of fields"},
            options={"title": "Schema Fields Utilization", "height": 300},
        )

    else:
        # ##### Create comparation graphics #######
        graphics["grouped_fields"] = bar_graphic(
            data=util_data["summary"],
            col_names=["group", "lab_values", "bio_values"],
            legend=["Metada lab", "Bio analysis"],
            yaxis={"title": "Number of fields"},
            options={"title": "Schema Fields Utilization", "height": 300},
        )

        #  ##### create metada lab analysis  ######
        graph_gauge_percent_values(
            app_name="lims_filled_values",
            value=util_data["lims_f_values"],
            label="Lab filled values %",
        )

    #  ##### create Bio info analysis  ######
    graph_gauge_percent_values(
        app_name="bio_filled_values",
        value=util_data["bio_f_values"],
        label="Bio filled values %",
        size=150,
    )
    # ##### create bar graph with all fields and values
    if "num_lab_fields" in util_data:
        lab_colors = ["#0099ff"] * util_data["num_lab_fields"]
        bio_colors = ["#1aff8c"] * util_data["num_bio_fields"]
        colors = lab_colors + bio_colors
    else:
        colors = None
    graphics["detailed_fields"] = bar_graphic(
        data=util_data["field_detail_data"],
        col_names=["field_name", "field_value"],
        legend=["metadata fields"],
        yaxis={"title": "Number of samples"},
        options={
            "title": "Number of samples for each schema field",
            "height": 400,
            "colors": colors,
        },
    )
    # ###### create table for detailed field information ######
    graphics["table"] = zip(
        util_data["field_detail_data"]["field_name"],
        util_data["field_detail_data"]["field_value"],
    )
    return graphics
