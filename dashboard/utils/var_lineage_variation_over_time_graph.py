# Generic imports
from datetime import datetime

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
from plotly.subplots import make_subplots

# Local imports
import dashboard.utils.generic_graphic_data
import dashboard.utils.generic_process_data


def create_lineages_variations_graphic():
    """Collect the pre-processed data from database"""
    json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
        "variant_graphic_data"
    )
    if json_data is None:
        # Execute the pre-processed task to get the data
        result = dashboard.utils.generic_process_data.pre_proc_variant_graphic()
        if "ERROR" in result:
            return result
        json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
            "variant_graphic_data"
        )

    data_df = pd.DataFrame(json_data)
    data_df = data_df.dropna()
    data_df["Collection date"] = pd.to_datetime(data_df["Collection date"])
    # TODO: Clean database so this date filter is not necessary
    data_df = data_df[data_df["Collection date"] >= "2020-01-01"]
    data_df["samples"] = data_df["samples"].astype(int)
    app = DjangoDash(
        "variationLineageOverTime", external_stylesheets=[dbc.themes.BOOTSTRAP]
    )
    first_date = data_df["Collection date"].min()
    last_date = data_df["Collection date"].max()
    # Order by date to ensure isoweeks are ordered too later on
    data_df = data_df.sort_values("Collection date")
    samples_df = pd.DataFrame()
    samples_df["samples"] = data_df.groupby("Collection date")["samples"].sum()
    samples_df = samples_df.reset_index()

    lineages = data_df["Lineage"].unique().tolist()
    # group samples in variants per weeks
    data_week_df = (
        data_df.groupby(["Lineage", pd.Grouper(key="Collection date", freq="W-MON")])[
            "samples"
        ]
        .sum()
        .reset_index()
        .sort_values("Collection date")
    )
    # Include all the weeks with no data as 0 samples
    full_weeks_as_str = pd.date_range(
        data_week_df["Collection date"].min(),
        data_week_df["Collection date"].max(),
        freq="W-MON",
    ).strftime("%G-W%V-%u")

    # Create a full DataFrame with the combination of all Lineages and all possible weeks
    df_full = pd.MultiIndex.from_product(
        [data_week_df["Lineage"].unique(), full_weeks_as_str],
        names=["Lineage", "Collection date"],
    ).to_frame(index=False)
    df_full["Collection date"] = pd.to_datetime(
        df_full["Collection date"], format="%G-W%V-%u"
    )

    # Merge with the original data and fill missing values with 0
    df_full = df_full.merge(
        data_week_df, on=["Lineage", "Collection date"], how="left"
    ).fillna(0)

    controls = dbc.Card(
        [
            html.Div(
                [
                    dbc.Label("Select period of time (MM/DD/YYYY)"),
                    dcc.DatePickerRange(
                        id="datePickerRange",
                        start_date_placeholder_text="Start Date",
                        end_date_placeholder_text="End Date",
                        min_date_allowed=first_date,
                        max_date_allowed=last_date,
                        calendar_orientation="horizontal",
                        number_of_months_shown=3,
                    ),
                ],
            ),
        ],
        body=True,
    )
    period_text = dbc.Card(
        [
            html.Div(
                "When no Selection period is set, data from the first registered date until today is shown"
            )
        ]
    )
    app.layout = dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(controls, md=4),
                    dbc.Col(period_text, md=6),
                    dbc.Col(
                        dcc.Graph(
                            id="lineageGraph",
                            figure="",
                            config={"displaylogo": False},
                            style={"padding-top": "15px"},
                        ),
                        md=12,
                    ),
                ],
                align="center",
            ),
        ],
        fluid=True,
    )

    @app.callback(
        Output("lineageGraph", "figure"),
        [Input("datePickerRange", "start_date"), Input("datePickerRange", "end_date")],
    )
    def update_graph(start_date, end_date):
        if start_date is None or end_date is None:
            # Select the samples from all registered years
            sub_data_df = df_full.loc[
                (df_full["Collection date"] >= first_date)
                & (df_full["Collection date"] < last_date)
            ]

        else:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
            sub_data_df = df_full.loc[
                (df_full["Collection date"] >= start_date_obj)
                & (df_full["Collection date"] < end_date_obj)
            ]

        sub_data_df["Collection ISOWeek"] = sub_data_df["Collection date"].dt.strftime(
            "%G-W%V"
        )

        graph_df = (
            sub_data_df.drop(["Collection date"], axis=1)
            .set_index(["Lineage", "Collection ISOWeek"])
            .unstack(["Lineage"])
        )

        # remove the sample text from column
        graph_df.columns = ["{}".format(t) for v, t in graph_df.columns]
        graph_df = graph_df.fillna(0)
        # Convert values to integer
        graph_df[lineages] = graph_df[lineages].astype(int)
        # Do the percentage calculation
        value_per_df = (graph_df.div(graph_df.sum(axis=1), axis=0) * 100).round(2)
        value_per_df = value_per_df.fillna(0)
        samples_per_week = graph_df.sum(axis=1)
        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        if sub_data_df.empty:
            fig.add_trace(go.Scatter())
            fig.add_annotation(
                text="No samples found for the selected dates",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=20, color="red"),
            )
            fig.update_layout(
                xaxis=dict(showline=True, linecolor="black", linewidth=2, mirror=True),
                yaxis=dict(showline=True, linecolor="black", linewidth=2, mirror=True),
                barmode="stack",
                hovermode="x unified",
                legend_xanchor="center",  # use center of legend as anchor
                legend_yanchor="top",
                legend_orientation="h",  # show entries horizontally
                legend_x=0.5,  # put legend in center of x-axis
                legend_y=-0.30,
                bargap=0,  # gap between bars of adjacent location coordinates.
                bargroupgap=0,  # gap between bars of the same location coordinate.
                margin_l=10,
                margin_r=10,
                margin_b=40,
                margin_t=40,
                height=600,
                paper_bgcolor="white",
                plot_bgcolor="white",
            )
            return fig
        hover_text = [f"{y}" for y in samples_per_week.values]
        fig.add_trace(
            go.Scatter(
                x=value_per_df.index,
                y=samples_per_week,
                hoverinfo="text",
                hovertemplate="%{text}",
                mode="lines",
                name="Number of samples",
                line_color="#0066cc",
                line_width=2,
                text=hover_text,
            ),
            secondary_y=True,
        )
        for lineage in lineages:
            # Setting hovertext to show values > 0 in bold
            hover_text = [
                (
                    f"<b>{lineage}: {y}%</b><extra></extra>"
                    if y > 0
                    else f"{lineage}: {y}%<extra></extra>"
                )
                for y in value_per_df[lineage].values
            ]
            fig.add_trace(
                go.Scatter(
                    x=value_per_df.index,
                    y=value_per_df[lineage],
                    hoverinfo="text",
                    hovertemplate="%{text}",
                    mode="lines",
                    name=lineage,
                    opacity=0.7,
                    stackgroup="variants",
                    text=hover_text,
                ),
                secondary_y=False,
            )
        # Set x-axis title
        fig.update_xaxes(
            title="Collection Date (ISOweeks)",
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
            title_text="Variants over the selected period",
            autotypenumbers="convert types",
            barmode="stack",
            hovermode="x unified",
            legend_xanchor="center",  # use center of legend as anchor
            legend_yanchor="top",
            legend_orientation="h",  # show entries horizontally
            legend_x=0.5,  # put legend in center of x-axis
            legend_y=-0.30,
            bargap=0,  # gap between bars of adjacent location coordinates.
            bargroupgap=0,  # gap between bars of the same location coordinate.
            margin_l=10,
            margin_r=10,
            margin_b=40,
            margin_t=40,
            height=600,
            paper_bgcolor="white",
            plot_bgcolor="white",
            xaxis=dict(showline=True, linecolor="black", linewidth=2, mirror=True),
            yaxis=dict(
                showline=True,
                linecolor="black",
                linewidth=2,
                mirror=True,
                ticksuffix=" ",
            ),
            yaxis2_tickprefix=" ",
        )
        return fig
