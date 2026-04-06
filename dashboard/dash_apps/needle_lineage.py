from dash import dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

import dashboard.utils.var_needle_mutation_graph_by_lineage

APP_NAME = "needlePlotMutationByLineage"


def register():
    app = DjangoDash(
        APP_NAME,
        external_stylesheets=[
            "https://fonts.googleapis.com/css2?family=Oxanium&display=swap",
            "/static/core/css/dash_style.css",
        ],
    )

    app.layout = html.Div(
        children=[
            html.Div(
                children=[
                    html.Div(
                        children=[
                            "Select Lineage",
                            dcc.Dropdown(
                                id="needleplot-select-lineage",
                                options=[],
                                clearable=False,
                                multi=False,
                                value=None,
                                style={"width": "150px", "margin-right": "30px"},
                            ),
                        ],
                        style={"margin-left": "20px"},
                    ),
                    html.Div(
                        [
                            "Show Range Slider",
                            dcc.Checklist(
                                id="toggle-rangeslider",
                                options=[{"label": "Enable", "value": "on"}],
                                value=["on"],
                                inline=True,
                            ),
                        ],
                        style={"margin-left": "20px"},
                    ),
                    html.Div(
                        children=[dcc.Markdown(id="samples_markdown")],
                        style={"margin-left": "50px"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "start",
                    "align-items": "flex-start",
                },
            ),
            html.Div(
                children=[
                    dcc.Loading(
                        id="loading_plot_wrapper",
                        type="default",
                        children=[
                            html.Div(
                                id="needleplot-container-div",
                                children=[
                                    dcc.Graph(
                                        id="needleplot-graph",
                                        style={"padding-top": "15px"},
                                        figure=dashboard.utils.var_needle_mutation_graph_by_lineage.empty_needle_plot_figure(),
                                    ),
                                ],
                                style={"position": "relative"},
                            )
                        ],
                        overlay_style={"visibility": "visible", "filter": "blur(1px)"},
                        parent_style={"position": "relative"},
                    ),
                ],
            ),
        ]
    )

    @app.callback(
        [Output("needleplot-graph", "figure"), Output("samples_markdown", "children")],
        [
            Input("needleplot-select-lineage", "value"),
            Input("toggle-rangeslider", "value"),
            Input("needleplot-graph", "relayoutData"),
        ],
    )
    def update_sample(selected_lineage, toggle_rangeslider, relayout_data):
        if not selected_lineage:
            return (
                dashboard.utils.var_needle_mutation_graph_by_lineage.empty_needle_plot_figure(),
                "No lineage selected",
            )
        return dashboard.utils.var_needle_mutation_graph_by_lineage.build_needle_plot_figure(
            selected_lineage,
            toggle_rangeslider=toggle_rangeslider,
            relayout_data=relayout_data,
        )
