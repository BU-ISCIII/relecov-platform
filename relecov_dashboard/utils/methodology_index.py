# import pandas as pd
from statistics import mean
from relecov_core.utils.handling_bioinfo_analysis import (
    get_bioinfo_analyis_fields_utilization,
)

from relecov_core.utils.schema_handling import (
    get_default_schema,
)  # , get_schema_properties

# from relecov_core.utils.rest_api_handling import get_summarize_data
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

import dash_html_components as html

import dash_daq as daq


def graph_never_used_fields(value, label):
    """Create Dashboard application for showing a gauge graphic for the never
    used fields
    """
    app = DjangoDash("never_used_fields", external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = html.Div(
        style={"font-size": "1.5rem", "color": "green"},
        children=[
            daq.Gauge(
                showCurrentValue=True,
                # color={"gradient":True,"ranges":{"red":[0,40],"yellow":[40,80],"green":[80,100]}},
                id="n_used_fields",
                label={"label": label, "style": {"font-size": "1.52rem"}},
                value=value,
                max=((value // 10) + 1) * 10,
                min=0,
            ),
        ],
    )


def graph_always_none(value, label):
    """Create Dashboard application for showing a gauge graphic for the never
    used fields
    """
    app = DjangoDash("always_none", external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = html.Div(
        style={"font-size": "1.5rem", "color": "green"},
        children=[
            daq.Gauge(
                showCurrentValue=True,
                color="#0066ff",
                id="n_used_fields",
                label={"label": label, "style": {"font-size": "1.52rem"}},
                value=value,
                max=((value // 10) + 1) * 10,
                min=0,
            ),
        ],
    )


def graph_filled_fields(value, label):
    """Create Dashboard application for showing a gauge graphic for the not
    empty fields values
    """
    app = DjangoDash("param_not_empty", external_stylesheets=[dbc.themes.BOOTSTRAP])
    if value <= 40:
        text_color = "red"
    elif value <= 75:
        text_color = "#e6e600"
    else:
        text_color = "green"
    app.layout = html.Div(
        style={"font-size": "1.5rem", "color": "green"},
        children=[
            daq.Gauge(
                showCurrentValue=True,
                color={
                    "default": text_color,
                    "gradient": True,
                    "ranges": {"red": [0, 40], "yellow": [40, 80], "green": [80, 100]},
                },
                id="my-gauge-1",
                label={"label": label, "style": {"font-size": "1.5rem"}},
                value=value,
                max=100,
                min=0,
            ),
        ],
    )


def graph_overall_filled_fieds(value, label):
    """Create Dashboard application for showing a gauge graphic for the not
    empty fields values
    """
    app = DjangoDash(
        "overall_filled_fields", external_stylesheets=[dbc.themes.BOOTSTRAP]
    )
    if value <= 40:
        text_color = "red"
    elif value <= 75:
        text_color = "#e6e600"
    else:
        text_color = "green"
    app.layout = html.Div(
        style={"font-size": "1.5rem", "color": "green"},
        children=[
            daq.Gauge(
                showCurrentValue=True,
                color={
                    "default": text_color,
                    "gradient": True,
                    "ranges": {"red": [0, 40], "yellow": [40, 80], "green": [80, 100]},
                },
                id="my-gauge-1",
                label={"label": label, "style": {"font-size": "1.5rem"}},
                value=value,
                max=100,
                min=0,
            ),
        ],
    )


def schema_fields_utilization():
    """ """
    schema_obj = get_default_schema()
    if schema_obj is None:
        return
    util_data = get_bioinfo_analyis_fields_utilization()

    # iskylims_fields = get_summarize_data({"sample_project": "Relecov"})
    sum_data = {}
    for schema_name in util_data.keys():
        sum_data["never_used"] = len(util_data[schema_name])
        sum_data["always_none"] = len(util_data[schema_name]["always_none"])
        f_values = []
        for value in util_data[schema_name]["fields"].values():
            f_values.append(value)
        if len(f_values) > 1:
            sum_data["f_values"] = float("%.1f" % (mean(f_values) * 100))
        else:
            sum_data["f_values"] = 0
        sum_data["overall"] = float(
            "%.1f"
            % (
                len(util_data[schema_name]["fields"])
                / util_data[schema_name]["num_fields"]
                * 100
            )
        )

    return sum_data


def index_dash_fields():
    graphics = {}
    sum_data = schema_fields_utilization()

    # create graphic for never useds fields
    graph_never_used_fields(sum_data["never_used"], "Never used fields")
    # create graphic for always None
    graph_always_none(sum_data["always_none"], "Always are None")
    # create the percentage filled fields
    graph_filled_fields(sum_data["f_values"], "Filled values fields %")
    # create overall set fields
    graph_overall_filled_fieds(sum_data["overall"], "Overall Filled fields %")

    return graphics
