# from datetime import datetime

# from time import strptime
import pandas as pd
from dash import dcc, html
from django_plotly_dash import DjangoDash

# from dash.dependencies import Input, Output
import plotly.graph_objects as go

from relecov_core.utils.handling_samples import (
    get_all_recieved_samples_with_dates,
)


def create_dataframe_from_database():
    """
    This function reads data from database, DateUpdateState model:
        - number of sample from "sampleID" field,
        - date from "date" field

    Returns a pandas dataframe object.
    """
    """
    # sample_objs = DateUpdateState.objects.all()
    sample_objs = DateUpdateState.objects.filter(stateID__iexact="Defined")
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
        date_converted = datetime(int(year), month, int(date_list[1]))
        list_of_dates.append(date_converted.strftime("%Y-%m-%d"))

    list_of_lists.append(list_of_samples)
    list_of_lists.append(list_of_dates)

    df = pd.DataFrame(list_of_lists).transpose()
    df.columns = ["SAMPLE", "DATE"]
    df = df.sort_values(by=["DATE"])
    """
    return


def display_received_samples_graph():
    """Fetch the number of samples received in the plaftorm and show them"""
    data = get_all_recieved_samples_with_dates()
    app = DjangoDash(name="TotalReceivedSamplesGraph")
    df = data
    app.layout = create_samples_received_over_time(df)

    # @app.callback(Output("graph-with-slider", "figure"), Input("date_slider", "value"))


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
    number_of_samples_per_date = pd.DataFrame(df.DATE.value_counts())

    # Create figure
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=dates_unique,
            y=number_of_samples_per_date["DATE"],
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
            y=number_of_samples_per_date["DATE"],
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
