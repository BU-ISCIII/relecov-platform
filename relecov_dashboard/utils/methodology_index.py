# import pandas as pd
from statistics import mean
from relecov_core.utils.handling_bioinfo_analysis import (
    get_bioinfo_analyis_fields_utilization,
)

from relecov_core.utils.schema_handling import (
    get_default_schema,
)

from relecov_core.utils.rest_api_handling import get_stats_data
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

import dash_html_components as html

import dash_daq as daq


def graph_gauge_percent_values(app_name, value, label):
    """Create Dashboard application for showing a gauge graphic for the not
    empty fields values
    """
    app = DjangoDash(app_name, external_stylesheets=[dbc.themes.BOOTSTRAP])
    if value <= 40:
        text_color = "red"
    elif value <= 75:
        text_color = "#e6e600"
    else:
        text_color = "green"
    app.layout = html.Div(
        daq.Gauge(
            showCurrentValue=True,
            color={
                "default": text_color,
                "gradient": True,
                "ranges": {"red": [0, 40], "yellow": [40, 80], "green": [80, 100]},
            },
            id="my-gauge-1",
            label={"label": label, "style": {"font-size": "1.5rem", "color": "green"}},
            value=value,
            max=100,
            min=0,
        ),
    )


def graph_gauge_value(app_name, value, label, color="#33bbff"):
    """Create Dashboard application for showing a gauge graphic for the never
    used fields
    """
    app = DjangoDash(app_name, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = html.Div(
        daq.Gauge(
            showCurrentValue=True,
            color=color,
            id="n_used_fields",
            label={"label": label, "style": {"font-size": "1.52rem", "color": "green"}},
            value=value,
            max=((value // 10) + 1) * 10,
            min=0,
        ),
    )


def schema_fields_utilization():
    """ """
    schema_obj = get_default_schema()
    if schema_obj is None:
        return

    # get stats utilization fields from LIMS
    lims_fields = get_stats_data({"sample_project_name": "Relecov"})
    if "ERROR" in lims_fields:
        lims_data = lims_fields
    else:
        lims_data = {}
        lims_data["always_none"] = len(lims_fields["always_none"])
        f_values = []
        for value in lims_fields["fields"].values():
            f_values.append(value)
        if len(f_values) > 1:
            lims_data["f_values"] = float("%.1f" % (mean(f_values) * 100))
        else:
            lims_data["f_values"] = 0
        lims_data["overall"] = float(
            "%.1f"
            % (
                len(lims_fields["fields"])
                / (
                    len(lims_fields["fields"])
                    + len(lims_fields["always_none"])
                    + len(lims_fields["never_used"])
                )
                * 100
            )
        )

    # get fields utilization from bioinfo analysis
    util_data = get_bioinfo_analyis_fields_utilization()

    bio_data = {}
    for schema_name in util_data.keys():
        bio_data["never_used"] = len(util_data[schema_name])
        bio_data["always_none"] = len(util_data[schema_name]["always_none"])
        f_values = []
        for value in util_data[schema_name]["fields"].values():
            f_values.append(value)
        if len(f_values) > 1:
            bio_data["f_values"] = float("%.1f" % (mean(f_values) * 100))
        else:
            bio_data["f_values"] = 0
        bio_data["overall"] = float(
            "%.1f"
            % (
                len(util_data[schema_name]["fields"])
                / util_data[schema_name]["num_fields"]
                * 100
            )
        )

    return lims_data, bio_data


def index_dash_fields():
    graphics = {}
    lims_data, bio_data = schema_fields_utilization()

    if "ERROR" in lims_data:
        graphics["lims_data"] = lims_data
    else:
        # ##### Create LIMS graphics #######
        graph_gauge_value(
            app_name="lims_always_none_fields",
            value=lims_data["always_none"],
            label="Always None fields",
            color="#0066ff",
        )
        graph_gauge_percent_values(
            app_name="lims_filled_values",
            value=lims_data["f_values"],
            label="Filled values fields %",
        )
        graph_gauge_percent_values(
            app_name="lims_overall_filled_values",
            value=lims_data["overall"],
            label="Overall Filled fields %",
        )
    #  #### create Bio info analysis  ######
    graph_gauge_value(
        app_name="bio_never_used_fields",
        value=bio_data["never_used"],
        label="Never used fields",
    )
    graph_gauge_value(
        app_name="bio_always_none",
        value=bio_data["always_none"],
        label="Always None fields",
        color="#0066ff",
    )
    graph_gauge_percent_values(
        app_name="bio_filled_values",
        value=bio_data["f_values"],
        label="Filled values fields %",
    )
    graph_gauge_percent_values(
        app_name="bio_overall_filled_fields",
        value=bio_data["overall"],
        label="Overall Filled fields %",
    )

    return graphics
