from statistics import mean

from relecov_core.utils.handling_bioinfo_analysis import (
    get_bioinfo_analyis_fields_utilization,
)
from relecov_core.utils.schema_handling import (
    get_default_schema,
)
from relecov_core.utils.rest_api_handling import get_stats_data
from relecov_dashboard.utils.plotly_graphics import bar_graphic
from relecov_dashboard.utils.dash_plotly_no_callback import graph_gauge_percent_values


def schema_fields_utilization():
    """ """
    schema_obj = get_default_schema()
    if schema_obj is None:
        return

    util_data = {"summary": {}}
    util_data["summary"]["group"] = ["Empty Fields", "Total Fields"]

    # get stats utilization fields from LIMS
    lims_fields = get_stats_data({"sample_project_name": "Relecov"})
    if "ERROR" in lims_fields:
        util_data["ERROR"] = lims_fields["ERROR"]
    else:
        f_values = []
        for value in lims_fields["fields"].values():
            f_values.append(value)
        if len(f_values) > 1:
            util_data["lims_f_values"] = float("%.1f" % (mean(f_values) * 100))
        else:
            util_data["lims_f_values"] = 0
        # Calculate empty fields and total fields
        empty_fields = len(lims_fields["always_none"]) + len(lims_fields["never_used"])
        total_fields = len(lims_fields["fields"]) + empty_fields
        util_data["summary"]["lab_values"] = [empty_fields, total_fields]

    # get fields utilization from bioinfo analysis
    bio_fields = get_bioinfo_analyis_fields_utilization()

    for schema_name in bio_fields.keys():
        f_values = []
        for value in bio_fields[schema_name]["fields"].values():
            f_values.append(value)
        if len(f_values) > 1:
            util_data["bio_f_values"] = float("%.1f" % (mean(f_values) * 100))
        else:
            util_data["bio_f_values"] = 0
        # Calculate empty fields and total fields for bio analysis fields
        empty_fields = len(bio_fields[schema_name]["always_none"]) + len(
            bio_fields[schema_name]["never_used"]
        )
        total_fields = len(bio_fields[schema_name]["fields"]) + empty_fields
    util_data["summary"]["bio_values"] = [empty_fields, total_fields]

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
            options={"title": "Schema Fields Utilization"},
        )
    else:
        # ##### Create comparation graphics #######
        graphics["grouped_fields"] = bar_graphic(
            data=util_data["summary"],
            col_names=["group", "lab_values", "bio_values"],
            legend=["Metada lab", "Bio analysis"],
            options={"title": "Schema Fields Utilization"},
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

    return graphics
