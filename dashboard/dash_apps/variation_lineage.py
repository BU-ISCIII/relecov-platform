import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

import dashboard.utils.var_lineage_variation_over_time_graph

APP_NAME = "variationLineageOverTime"


def register():
    data_df = (
        dashboard.utils.var_lineage_variation_over_time_graph.load_variant_graphic_dataframe()
    )
    if isinstance(data_df, dict) or data_df.empty:
        first_date = None
        last_date = None
        initial_figure = {}
    else:
        first_date = data_df["Collection date"].min()
        last_date = data_df["Collection date"].max()
        df_full = dashboard.utils.var_lineage_variation_over_time_graph.prepare_variant_graphic_dataframe(
            data_df
        )
        initial_figure = dashboard.utils.var_lineage_variation_over_time_graph.build_lineage_variation_figure(
            df_full
        )

    app = DjangoDash(
        APP_NAME,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )

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
                            figure=initial_figure,
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
        data_df = (
            dashboard.utils.var_lineage_variation_over_time_graph.load_variant_graphic_dataframe()
        )
        if isinstance(data_df, dict) or data_df.empty:
            return initial_figure
        df_full = dashboard.utils.var_lineage_variation_over_time_graph.prepare_variant_graphic_dataframe(
            data_df
        )
        return dashboard.utils.var_lineage_variation_over_time_graph.build_lineage_variation_figure(
            df_full, start_date=start_date, end_date=end_date
        )
