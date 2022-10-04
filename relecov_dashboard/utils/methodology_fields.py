# import pandas as pd
from statistics import mean
from relecov_core.utils.handling_bioinfo_analysis import (
    get_bioinfo_analyis_fields_utilization,
)

# from relecov_core.utils.handling_samples import get_samples_count_per_schema

import urllib.request as urlreq
import json

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
import dash_bio as dashbio
import dash_daq as daq


def graph_not_empty_fields(value, label):
    """Create Dashboard application for showing a gauge graphic for the not
    empty fields values
    """
    app = DjangoDash("param_not_empty", external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = html.Div(
        style={"font-size": "2rem", "color": "green"},
        children=[
            daq.Gauge(
                showCurrentValue=True,
                color={
                    "gradient": True,
                    "ranges": {"red": [0, 40], "yellow": [40, 80], "green": [80, 100]},
                },
                id="my-gauge-1",
                label={"label": label, "style": {"font-size": "2rem"}},
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
        style={"font-size": "2rem", "color": "green"},
        children=[
            daq.Gauge(
                showCurrentValue=True,
                # color={"gradient":True,"ranges":{"red":[0,40],"yellow":[40,80],"green":[80,100]}},
                id="n_used_fields",
                label={"label": label, "style": {"font-size": "2rem"}},
                value=value,
                max=10,
                min=0,
            ),
        ],
    )

    @app.callback(Output("n_used_fields", "value"), Input("my-gauge-slider-1", "value"))
    def update_output(value):
        return value


def create_utilization_graphic(lineage):
    data = urlreq.urlopen("https://git.io/needle_PIK3CA.json").read().decode("utf-8")

    mdata = json.loads(data)
    # app = DjangoDash("m_utilization")
    app = DjangoDash("m_utilization", external_stylesheets=[dbc.themes.BOOTSTRAP])
    control1 = dbc.Card(
        [
            html.Div(
                [
                    dbc.Label("X variable"),
                    dcc.Dropdown(
                        id="x-variable",
                        options=[
                            {"label": "a", "value": 1},
                            {"label": "b", "value": 1},
                        ],
                    ),
                ]
            ),
        ],
        body=True,
    )

    control2 = dbc.Card(
        [
            html.Div(
                [
                    dbc.Label("Y variable"),
                    dcc.Dropdown(
                        id="y-variable",
                        options=[
                            {"label": "cc", "value": 1},
                            {"label": "dd", "value": 1},
                        ],
                        value="cc",
                    ),
                ]
            ),
        ],
        body=True,
    )

    graphic = dbc.Card(
        [
            html.Div(
                [
                    dcc.Dropdown(
                        id="dashbio-default-needleplot",
                        options=[
                            {"label": "Show", "value": 1},
                            {"label": "Hide", "value": 0},
                        ],
                        clearable=False,
                        multi=False,
                        value=1,
                        style={"width": "300px"},
                    ),
                    "Select a Lineage",
                    dashbio.NeedlePlot(
                        id="dashbio-default-needleplot", mutationData=mdata
                    ),
                ]
            ),
        ],
        body=True,
    )

    app.layout = dbc.Container(
        [
            dbc.Card(
                children=[
                    dbc.CardBody(html.H2("Iris k-means clustering")),
                    html.H1("Iris k-means clustering"),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(control1, md=4),
                    dbc.Col(control2, md=4),
                    # dbc.Col(dcc.Graph(id="cluster-graph"), md=8),
                    dbc.Col(graphic, md=12),
                ],
                align="center",
            ),
        ],
        fluid=True,
    )
    """
            dcc.Dropdown(
                id='dashbio-default-needleplot',
                options=[{"label": "Show", "value": 1}, {"label": "Hide", "value": 0}],
                clearable=False,
                multi=False,
                value=1,
                style={"width": "400px"},
            ),
            "Select a Lineage",
            dashbio.NeedlePlot(
                id='dashbio-default-needleplot',
                mutationData=mdata
            )
        ]
    )
    """
    # import pdb; pdb.set_trace()

    @app.callback(
        Output("dashbio-needleplot", "mutationData"),
        Input("x-variable", "value"),
        Input("y-variable", "value"),
    )
    def update_sample(selected_lineage):
        print(selected_lineage)

        create_utilization_graphic(selected_lineage)
        mdata = create_utilization_graphic(selected_lineage)
        mutation_data = mdata
        return mutation_data

    @app.callback(
        Output("dashbio-needleplot", "rangeSlider"),
        Input("needleplot-rangeslider", "value"),
    )
    def update_range_slider(range_slider_value):
        print("valor de range ", range_slider_value)
        return True if range_slider_value else False


def schema_fields_utilization():
    """ """
    schema_fields = get_bioinfo_analyis_fields_utilization()
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
    return value, sum_never_used


def index_dash_fields():
    f_value, n_used = schema_fields_utilization()
    graph_not_empty_fields(f_value, "Bioinfo metadata filled values %")
    # create_utilization_graphic(1)
    # return render(request, "relecov_dashboard/methodologytest.html" )
    graph_never_used_fields(n_used, "Never used bioinfometada fields")
    return
