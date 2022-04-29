from unicodedata import name
from django.shortcuts import render
#from plotly.offline import plot
#import plotly.graph_objects as go

# plotly dash
import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash

# import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

#from dash import Input, Output#Dash, dcc, html,
from dash.dependencies import Input, Output
import dash
import os
from django.conf import settings

#import dash_bootstrap_components as dbc

# IMPORT FROM UTILS
from relecov_core.utils.random_data import *
from relecov_core.utils.parse_files import *
from relecov_core.utils.dashboard import *


def index(request):
    variant_data = parse_csv_into_list_of_dicts(
        os.path.join(settings.BASE_DIR, "relecov_core", "docs", "variantLuisTableCSV.csv")
    )

    # app = DjangoDash(name= "VariantGraph", external_stylesheets=[dbc.themes.BOOTSTRAP])
    app = DjangoDash(name= "VariantGraph")   # replaces dash.Dash

    app.layout = get_variant_graph(variant_data)

    @app.callback(
    Output('graph-with-slider', 'figure'),
    Input('week-slider', 'value'))

    def update_figure(selected_range):
        print('You have selected "{}"'.format(selected_range))

        df = set_dataframe_range_slider(variant_data, selected_range)

        fig = px.bar(df, x="Week", y="Sequences", color="Variant", barmode="stack",
                        hover_name="Variant")

        fig.update_layout(transition_duration=500)
        return fig

    return render(request, "relecov_dashboard/index.html")


def index2(request):
    max_weeks=0
    selected_range =[1,19]
    df_table = pd.read_csv(os.path.join(settings.BASE_DIR, "relecov_core", "docs", "cogUK", "table_3_2022-04-12.csv"))

    variant_data = parse_csv_into_list_of_dicts(
        "relecov_core/docs/variantLuisTableCSV.csv"
    )
    df = set_dataframe_range_slider(variant_data,selected_range)

    for week in df['Week'].unique():
        max_weeks += 1

    # app = DjangoDash("SimpleExampleRangeSlider", external_stylesheets=[dbc.themes.BOOTSTRAP])  # replaces dash.Dash
    app = DjangoDash("SimpleExampleRangeSlider")  # replaces dash.Dash
    fig = px.bar(df, x="Week", y="Sequences", color="Variant", barmode="stack")

    app.layout = html.Div(
        className="card",
        children=[
            html.Div(
                className="card-body bg-light",
                children=[
                    html.H1(
                        className="card-title",
                        children="VOCs/VUIs in Spain",
                    ),
                    html.Div(
                        className="card-text",
                        children="Variant data.",
                    ),
                ]
            ),

            html.Div(
                children=[
                    html.Div(
                        children=[
                            dcc.Graph(
                                className = "card",
                                id="graph-with-slider",
                                figure=fig

                            )
                        ]
                    )
                ]
            ),
            html.Br(),
            html.Div(
               children = dcc.RangeSlider(
                    min = df["Week"].min(),
                    max = max_weeks,
                    step="1",
                    value=[int(df["Week"].min()),max_weeks],
                    marks={str(week): str(week) for week in df['Week'].unique()},
                    id='week-slider'
                ),

            ),
            html.Div(
                className="card bg-light",
                children=[
                    html.Div(
                        className="card-body",
                        children=[
                            html.H3(
                            children="Variants of concern (VOC) and under investigation (VUI) detected in the Spain data.",
                            className="card-title"
                            ),
                            html.H5(
                                children="DISCLAIMER: relecov-platform uses curated sequences for determining the counts of a given lineage. Other sources of information may be reporting cases with partial sequence information or other forms of PCR testing.",
                                className="card-text"
                            )

                        ]
                    )
                ]
            ),
            html.Div(
                children=generate_table(df_table),
            )
       ]
    )

    @app.callback(
    Output('graph-with-slider', 'figure'),
    Input('week-slider', 'value'))

    def update_figure(selected_range):
        print('You have selected "{}"'.format(selected_range))

        df = set_dataframe_range_slider(variant_data, selected_range)

        fig = px.bar(df, x="Week", y="Sequences", color="Variant", barmode="stack",
                        hover_name="Variant")

        fig.update_layout(transition_duration=500)
        return fig

    return render(request, "relecov_dashboard/index2.html")

def index3(request):
    # app = DjangoDash( name= 'SimpleExampleBootstrap', external_stylesheets=[dbc.themes.BOOTSTRAP])
    app = DjangoDash( name= 'SimpleExampleBootstrap')

    app.layout = dbc.Container(
        dbc.Alert("Hello Bootstrap!", color="success"),
        className="p-5",
    )
    return render(request,"relecov_dashboard/index3.html")
