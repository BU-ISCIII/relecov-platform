# Generic imports
import datetime
import json
import os
from time import strptime

import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output
from django.conf import settings
from django_plotly_dash import DjangoDash

# Local imports
import core.models


def create_dataframe_from_database():
    """
    This function reads data from database, DateUpdateState model:
        - number of sample from "sampleID" field,
        - date from "date" field

    Returns a pandas dataframe object.
    """

    # sample_objs = DateUpdateState.objects.all()
    sample_objs = core.models.DateUpdateState.objects.filter(stateID__iexact="Defined")
    date_list = []
    list_of_dates = []
    list_of_samples = []
    list_of_lists = []
    for sample_obj in sample_objs:
        list_of_samples.append(sample_obj.get_sample_id())

        # Changes date format to "23 Aug, 2022" to "2022-08-23"
        date = sample_obj.get_date()
        date_list = date.split(",")
        year = date_list[1]
        date_list = date_list[0].split(" ")
        month = strptime(date_list[0], "%B").tm_mon
        date_converted = datetime.datetime(int(year), month, int(date_list[1]))
        list_of_dates.append(date_converted.strftime("%Y-%m-%d"))

    list_of_lists.append(list_of_samples)
    list_of_lists.append(list_of_dates)

    df = pd.DataFrame(list_of_lists).transpose()
    df.columns = ["SAMPLE", "DATE"]
    df = df.sort_values(by=["DATE"])

    return df


def create_dataframe_from_json():
    """
    This function reads data from processed_converted_metadata_lab.json:
        - number of sample from "isolate_sample_id" field,
        - date from "sample_received_date" field

    Returns a pandas dataframe object.
    """

    list_of_samples = []
    list_of_dates = []
    list_of_lists = []
    input_file = os.path.join(
        settings.BASE_DIR,
        "core",
        "docs",
        "processed_converted_metadata_lab.json",
    )
    with open(input_file, encoding="utf-8") as fh:
        data = json.load(fh)

    for line in data:
        # FIXME: isolate_sample_id has been changed for sequencing_sample_id as reference ID
        list_of_samples.append(line["isolate_sample_id"])
        # FIXME: sample_received_date is not mandatory
        list_of_dates.append(line["sample_received_date"])

    list_of_lists.append(list_of_samples)
    list_of_lists.append(list_of_dates)

    df = pd.DataFrame(list_of_lists).transpose()
    df.columns = ["SAMPLE", "DATE"]
    df = df.sort_values(by=["DATE"])

    return df


def create_samples_over_time_graph(df):
    app = DjangoDash(name="SamplesInTimeGraph")
    app.layout = create_samples_received_over_time(df)

    @app.callback(Output("graph-with-slider", "figure"), Input("date_slider", "value"))
    def update_samples_in_time_figure(selected_range):
        # df = create_dataframe_from_database()
        df = create_dataframe_from_json()
        return update_figure(df)


def create_samples_received_over_time(df):
    dates_unique = df["DATE"].unique()
    fig = update_figure(df)

    return html.Div(
        className="card",
        children=[
            html.Div(
                className="card-body bg-dark",
                children=[
                    html.H1(
                        className="card-title",
                        children="Samples in Spain",
                    ),
                    html.Div(
                        className="card-text",
                        children="Samples received over time.",
                    ),
                ],
            ),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            dcc.Graph(
                                className="card",
                                id="graph-with-slider",
                                figure=fig,
                            )
                        ]
                    )
                ]
            ),
            html.Br(),
            html.Div(
                children=dcc.RangeSlider(
                    id="date_slider",
                    min=dates_unique.min(),
                    max=dates_unique.max(),
                    step=None,
                    value=None,
                    # value=[int(df["Week"].min()), max_weeks],
                    marks=None,
                ),
            ),
        ],
    )


def update_figure(df):
    dates_unique = df["DATE"].unique()
    number_of_samples_per_date = df["DATE"].value_counts().to_dict()

    # Create figure
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=dates_unique,
            y=[number_of_samples_per_date[date] for date in dates_unique],
            name="Samples in time",
            marker_color="green",
            opacity=0.4,
            marker_line_color="rgb(8,48,107)",
            marker_line_width=2,
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=dates_unique,
            y=[number_of_samples_per_date[date] for date in dates_unique],
            mode="lines",
            line=dict(color="red"),
            name="Number of samples",
        ),
    )

    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list(
                    [
                        dict(
                            count=1, label="1 month", step="month", stepmode="backward"
                        ),
                        dict(
                            count=6, label="6 months", step="month", stepmode="backward"
                        ),
                        dict(count=1, label="1 year", step="year", stepmode="backward"),
                        dict(step="all"),
                    ]
                )
            ),
            rangeslider=dict(visible=True),
            type="date",
        )
    )

    fig.update_layout(transition_duration=500)

    return fig
