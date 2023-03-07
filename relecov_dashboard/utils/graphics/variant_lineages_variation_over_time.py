import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

from dash import dcc, html
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output

from relecov_dashboard.utils.generic_functions import get_graphic_json_data

from relecov_dashboard.utils.pre_processing_data import pre_proc_variant_graphic


def create_lineages_variations_graphic(date_range=None):
    """Collect the pre-processed data from database"""
    json_data = get_graphic_json_data("variant_graphic_data")
    if json_data is None:
        # Execute the pre-processed task to get the data
        result = pre_proc_variant_graphic()
        if "ERROR" in result:
            return result
        json_data = get_graphic_json_data("variant_graphic_data")

    data_df = pd.DataFrame(json_data)

    data_df["Collection date"] = pd.to_datetime(data_df["Collection date"])
    data_df["samples"] = data_df["samples"].astype(int)

    app = DjangoDash(
        "variationLineageOverTime", external_stylesheets=[dbc.themes.BOOTSTRAP]
    )
    # plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    controls = dbc.Card(
        [
            html.Div(
                [
                    dbc.Label("Select period of time"),
                    dcc.Dropdown(
                        id="periodTime",
                        options=[
                            {"label": "Select Period", "value": ""},
                            {"label": "Last year2", "value": "730"},
                            {"label": "Last 6 months", "value": "180"},
                            {"label": "Last month", "value": "30"},
                        ],
                    ),
                ]
            ),
        ],
        body=True,
    )
    app.layout = dbc.Container(
        [
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(controls, md=4),
                    dbc.Col(
                        dcc.Graph(
                            id="lineageGraph", figure="", config={"displaylogo": False}
                        ),
                        md=12,
                    ),
                ],
                align="center",
            ),
        ],
        fluid=True,
    )
    # return None
    # return plot_div

    @app.callback(
        Output("lineageGraph", "figure"),
        Input("periodTime", "value"),
    )
    def update_graph(periodTime):
        if periodTime is None or periodTime == "":
            # Select the samples from year 2021
            sub_data_df = data_df.loc[
                (data_df["Collection date"] >= "2021-01-01")
                & (data_df["Collection date"] < "2021-12-31")
            ]
        else:
            n_days = int(periodTime)
            sub_data_df = data_df.loc[
                (
                    data_df["Collection date"]
                    >= datetime.today() - timedelta(days=n_days)
                )
                & (data_df["Collection date"] < datetime.today())
            ]

        samples_df = pd.DataFrame()
        
        samples_df["samples"] = sub_data_df.groupby("Collection date")["samples"].sum()
        # convert groupby output Series to DataFrame
        # samples_df = samples_df.reset_index()
        samples_df["samples_moving_mean"] = samples_df["samples"].rolling(7).mean()
        # samples_df["Collection date"] = samples_df.index
        lineages = sub_data_df["Lineage"].unique().tolist()

        graph_df = sub_data_df.set_index(["Lineage", "Collection date"]).unstack(
            ["Lineage"]
        )
        graph_df.columns = ["{}".format(t) for v, t in graph_df.columns]
        graph_df = graph_df.fillna(0)
        # Convert values to integer
        graph_df[lineages] = graph_df[lineages].astype(int)
        # Do the percentage calculation
        value_per_df = graph_df.div(graph_df.sum(axis=1), axis=0) * 100

        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(
                x=samples_df.index,
                y=samples_df["samples_moving_mean"],
                mode="lines",
                line_color="#0066cc",
                line_width=2,
                name="Number of samples processed",
            ),
            secondary_y=True,
        )
        for lineage in lineages:
            fig.add_trace(
                go.Bar(
                    x=value_per_df.index,
                    y=value_per_df[lineage],
                    name=lineage,
                    opacity=0.7,
                ),
                secondary_y=False,
            )

        # Set x-axis title
        fig.update_xaxes(
            title_text="Collection Date",
        )

        # Set y-axes titles
        fig.update_yaxes(
            range=[0, 100], title_text="<b>Lineage % relative", secondary_y=False
        )
        fig.update_yaxes(
            title_text="<b>Number of samples processed</b>", secondary_y=True
        )

        # Add figure title
        fig.update_layout(
            title_text="Lineage variation over time 1 year",
            barmode="stack",
            hovermode="x unified",
            legend_xanchor="center",  # use center of legend as anchor
            legend_orientation="h",  # show entries horizontally
            legend_x=0.5,  # put legend in center of x-axis
            bargap=0,  # gap between bars of adjacent location coordinates.
            bargroupgap=0,  # gap between bars of the same location coordinate.
            margin_l=10,
            margin_r=10,
            margin_b=40,
            margin_t=30,
            height=800,
        )
        return fig
