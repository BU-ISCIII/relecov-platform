# import pandas as pd
from statistics import mean
from relecov_core.utils.handling_bioinfo_analysis import (
    get_bioinfo_analyis_fields_utilization,
)

from relecov_core.utils.schema_handling import get_default_schema, get_schema_properties
from relecov_core.utils.rest_api_handling import get_summarize_data
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc

import dash_html_components as html
from dash.dependencies import Input, Output

import dash_daq as daq


def graph_not_empty_fields(value, label):
    """Create Dashboard application for showing a gauge graphic for the not
    empty fields values
    """
    app = DjangoDash("param_not_empty", external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = html.Div(
        style={"font-size": "1.5rem", "color": "green"},
        children=[
            daq.Gauge(
                showCurrentValue=True,
                color={
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

    @app.callback(Output("my-gauge-1", "value"), Input("my-gauge-slider-1", "value"))
    def update_output(value):
        return value


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
                max=10,
                min=0,
            ),
        ],
    )

    @app.callback(Output("n_used_fields", "value"), Input("my-gauge-slider-1", "value"))
    def update_output(value):
        return value


def schema_fields_utilization():
    """ """
    schema_obj = get_default_schema()
    if schema_obj is None:
        return
    schema_fields = get_bioinfo_analyis_fields_utilization()
    iskylims_fields = get_summarize_data({"sample_project": "Relecov"})
    print(iskylims_fields)
    for schema_name, fields in schema_fields.items():
        # import pdb; pdb.set_trace()

        # field_df = pd.DataFrame(fields, index=0)
        # field_df = field_df.div(s_count).round(2)
        sum_never_used = 0
        f_values = []
        for value in fields.values():
            if value == "never_used":
                sum_never_used += 1
            else:
                f_values.append(value)
        value = int("%.0f" % (mean(f_values) * 100))
    # graph_not_empty_fields(value)
    # match once fields are collected from different ways
    get_schema_properties(schema_obj)
    return value, sum_never_used


def index_dash_fields():
    f_value, n_used = schema_fields_utilization()
    # create the app for percentage used fields
    graph_not_empty_fields(f_value, "Bioinfo metadata filled values %")
    # create graphic for never useds fields
    graph_never_used_fields(n_used, "Never used bioinfometada fields")
    # create sequencer pie graphic

    return
