# Generic imports
import json
from statistics import mean

# Local imports
import core.utils.bioinfo_analysis
import core.utils.rest_api
import core.utils.samples
import core.utils.schema
import dashboard.dashboard_config
import dashboard.utils.plotly
from dashboard.models import GraphicJsonFile


def _read_cached_bioinfo_util():
    """
    Returns the pre-baked JSON of bioinfo field usage,
    or None if it does not yet exist.
    """
    try:
        obj = GraphicJsonFile.objects.filter(
            graphic_name="methodology_bioinfo_fields"
        ).latest("creation_date")

        data = obj.graphic_data
        if isinstance(data, str):
            data = json.loads(data)
        return data

    except GraphicJsonFile.DoesNotExist:
        return None


def schema_fields_utilization():
    """Return ERROR when no connection to iSkyLIMS, NO_SCHEMA when there is
    no schema loaded yet, or the data to display graphic
    """
    schema_obj = core.utils.schema.get_default_schema()
    if schema_obj is None:
        return {"NO_SCHEMA": dashboard.dashboard_config.ERROR_NO_SCHEMA_DEFINED}

    util_data = {"summary": {}}
    util_data["summary"]["group"] = ["Empty Fields", "Total Fields"]
    util_data["field_detail_data"] = {
        "field_name": [],
        "field_value": [],
        "percent": [],
    }
    # get stats utilization fields from LIMS
    lims_fields = core.utils.rest_api.get_stats_data({"sample_project_name": "Relecov"})
    if "ERROR" in lims_fields:
        util_data["ERROR"] = lims_fields["ERROR"]
    else:
        f_values = []
        lims_field_display_map = (
            core.utils.rest_api.get_sample_project_field_display_map("Relecov")
        )
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

        # get the maximum to make the percentage of filled
        max_value = max(set(lims_fields["fields_value"].values()))
        for key, val in lims_fields["fields_value"].items():
            util_data["field_detail_data"]["field_name"].append(
                lims_field_display_map.get(key, key)
            )
            util_data["field_detail_data"]["field_value"].append(val)
            util_data["field_detail_data"]["percent"].append(max_value)
        util_data["num_lab_fields"] = len(lims_fields["fields_value"])

    # get fields utilization from bioinfo analysis
    bio_fields = (
        _read_cached_bioinfo_util()
        or core.utils.bioinfo_analysis.get_bioinfo_analyis_fields_utilization()
    )
    # if return an empty value skip looking for data
    if not bool(bio_fields):
        util_data["ERROR_ANALYSIS"] = "Not Data to process"
        return util_data

    # Calculate bio_f_values
    num_samples_in_sch = core.utils.samples.get_samples_count()
    num_fields = len(bio_fields["fields_value"])
    total_filled_values = sum(bio_fields["fields_value"].values())
    total_possible_values = num_fields * num_samples_in_sch
    bio_f_values = (
        (total_filled_values / total_possible_values) * 100
        if total_possible_values > 0
        else 0
    )
    util_data["bio_f_values"] = float("%.1f" % bio_f_values)

    # Calculate empty fields and total fields for bio analysis fields
    empty_fields = len(bio_fields["always_none"]) + len(bio_fields["never_used"])
    total_fields = len(bio_fields["fields_norm"]) + empty_fields
    util_data["summary"]["bio_values"] = [empty_fields, total_fields]
    # get the maximum from bio fields to make the percentage of filled
    max_value = max(set(bio_fields["fields_value"].values()))
    for key, val in bio_fields["fields_value"].items():
        util_data["field_detail_data"]["field_name"].append(key)
        util_data["field_detail_data"]["field_value"].append(val)
        util_data["field_detail_data"]["percent"].append(max_value)
    util_data["num_bio_fields"] = len(bio_fields["fields_value"])

    return util_data


def index_dash_fields():
    graphics = {}
    util_data = schema_fields_utilization()
    progress_bars = []

    if "NO_SCHEMA" in util_data:
        graphics["NO_SCHEMA"] = util_data["NO_SCHEMA"]
        return graphics
    if "ERROR" in util_data:
        graphics["ERROR"] = util_data["ERROR"]
        # Check if bioinfo data are present
        if "ERROR_ANALYSIS" in util_data:
            graphics["ERROR_ANALYSIS"] = util_data["ERROR_ANALYSIS"]
            return graphics
        graphics["grouped_fields"] = dashboard.utils.plotly.bar_graphic(
            data=util_data["summary"],
            col_names=["group", "bio_values"],
            legend=["Bioinformatic analysis"],
            yaxis={"title": "Number of fields"},
            options={"title": "Data Field Completeness", "height": 300},
        )

    else:
        #  ##### create metadata lab analysis  ######
        progress_bars.append(
            dashboard.utils.plotly.progress_bar(
                app_name="lims_filled_values",
                value=util_data["lims_f_values"],
                label="Laboratory Data Completeness",
            )
        )
        # ##### Create comparison graphics #######
        if "ERROR_ANALYSIS" in util_data:
            graphics["grouped_fields"] = dashboard.utils.plotly.bar_graphic(
                data=util_data["summary"],
                col_names=["group", "lab_values"],
                legend=["Laboratory metadata"],
                yaxis={"title": "Number of fields"},
                options={"title": "Data Field Completeness", "height": 300},
            )
        else:
            graphics["grouped_fields"] = dashboard.utils.plotly.bar_graphic(
                data=util_data["summary"],
                col_names=["group", "lab_values", "bio_values"],
                legend=["Laboratory metadata", "Bioinformatic analysis"],
                yaxis={"title": "Number of fields"},
                options={"title": "Data Field Completeness", "height": 300},
            )

    if "ERROR_ANALYSIS" not in util_data:
        #  ##### create Bio info analysis  ######
        progress_bars.append(
            dashboard.utils.plotly.progress_bar(
                app_name="bio_filled_values",
                value=util_data["bio_f_values"],
                label="Bioinformatics Data Completeness",
            )
        )
        # ##### create bar graph with all fields and values
        if "num_lab_fields" in util_data:
            lab_colors = ["#448873"] * util_data["num_lab_fields"]
            bio_colors = ["#809dd4"] * util_data["num_bio_fields"]
            colors = lab_colors + bio_colors
        else:
            colors = None
        graphics["detailed_fields"] = dashboard.utils.plotly.bar_graphic(
            data=util_data["field_detail_data"],
            col_names=["field_name", "field_value"],
            legend=["metadata fields"],
            yaxis={"title": "Number of samples"},
            options={
                "title": "Sample Count per Schema Field",
                "height": 400,
                "colors": colors,
                "truncate_labels": 15,
                "wrap_labels": None,
            },
        )
        # ###### create table for detailed field information ######
        graphics["table"] = zip(
            util_data["field_detail_data"]["field_name"],
            util_data["field_detail_data"]["field_value"],
            util_data["field_detail_data"]["percent"],
        )
    else:
        graphics["ERROR_ANALYSIS"] = util_data["ERROR_ANALYSIS"]

    graphics["progress_bars"] = progress_bars
    return graphics
