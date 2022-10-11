import os
import pandas as pd
import json
import plotly.express as px
import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash

# from dash.dependencies import Input, Output
from relecov_platform import settings


def parse_json_file():
    """
    This function loads a json file and returns a python dictionary.
    """

    input_file = os.path.join(
        settings.BASE_DIR,
        "relecov_core",
        "docs",
        "data_for_geomap_from_ISkyLims.json",
    )
    with open(input_file) as f:
        data = json.load(f)

    return data


def create_samples_per_ccaa_dataframe(data):
    list_of_lists = []

    region_data = data["region"]
    list_of_ccaa_names = region_data.keys()
    list_of_number_of_samples_per_ccaa = region_data.values()

    list_of_lists.append(list_of_ccaa_names)
    list_of_lists.append(list_of_number_of_samples_per_ccaa)

    df = pd.DataFrame(list_of_lists).transpose()
    df.columns = ["CCAA_NAME", "NUMBER_OF_SAMPLES"]
    df = df.sort_values(by=["NUMBER_OF_SAMPLES"])

    return df


def create_samples_per_laboratory_dataframe(data):
    list_of_lists = []

    laboratory_data = data["laboratory"]
    list_of_laboratory_names = laboratory_data.keys()
    list_of_number_of_samples_per_laboratory = laboratory_data.values()

    list_of_lists.append(list_of_laboratory_names)
    list_of_lists.append(list_of_number_of_samples_per_laboratory)

    df = pd.DataFrame(list_of_lists).transpose()
    df.columns = ["LABORATORY_NAME", "NUMBER_OF_SAMPLES"]
    df = df.sort_values(by=["NUMBER_OF_SAMPLES"])

    return df


def create_samples_received_over_time_per_ccaa_pieChart(data):
    df_per_ccaa = create_samples_per_ccaa_dataframe(data)

    fig = px.pie(
        df_per_ccaa,
        values="NUMBER_OF_SAMPLES",
        names="CCAA_NAME",
        title="Samples received per CCAA",
        labels={
            "CCAA_NAME": "CCAA",
            "NUMBER_OF_SAMPLES": "NUMBER OF SAMPLES",
        },
        hole=0.2,
        color_discrete_sequence=px.colors.sequential.Sunset,
    )

    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    app = DjangoDash("samplesReceivedOverTimePerCCAAPie")
    app.layout = html.Div(
        className="card",
        children=[
            html.Div(
                className="card-body bg-dark",
                children=[
                    html.H1(
                        className="card-title",
                        children="Samples received in Spain",
                    ),
                    html.Div(
                        className="card-text",
                        children="Samples received by Autonomous Community",
                    ),
                ],
            ),
            html.Br(),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            dcc.Graph(
                                className="card",
                                # id="geomap-per-lineage",
                                id="samples_received_per_ccaa",
                                figure=fig,
                            )
                        ]
                    )
                ]
            ),
        ],
    )


def create_samples_received_over_time_per_laboratory_pieChart(data):
    df_per_laboratory = create_samples_per_laboratory_dataframe(data)

    fig = px.pie(
        df_per_laboratory,
        values="NUMBER_OF_SAMPLES",
        names="LABORATORY_NAME",
        title="Samples received per Laboratory",
        labels={
            "LABORATORY_NAME": "LABORATORY",
            "NUMBER_OF_SAMPLES": "NUMBER OF SAMPLES",
        },
        hole=0.2,
        color_discrete_sequence=px.colors.sequential.RdBu,
        # color_discrete_sequence=px.colors.sequential.Sunset,
    )

    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    app = DjangoDash("samplesReceivedOverTimePerLaboratoryPie")
    app.layout = html.Div(
        className="card mt-1",
        children=[
            html.Div(
                className="card-body bg-dark",
                children=[
                    html.H1(
                        className="card-title",
                        children="Samples received in Spain",
                    ),
                    html.Div(
                        className="card-text",
                        children="Samples received by Laboratory",
                    ),
                ],
            ),
            html.Br(),
            html.Br(),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            dcc.Graph(
                                className="card",
                                # id="geomap-per-lineage",
                                id="samples_received_per_laboratory",
                                figure=fig,
                            )
                        ]
                    )
                ]
            ),
        ],
    )
