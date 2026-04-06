from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash

import core.utils.plotly_graphics


APP_NAME = "sampleVariantGraphic"


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
                                    dcc.Store(id="mdata-store", data={}),
                                    dcc.Graph(
                                        id="needleplot-graph",
                                        style={"padding-top": "15px"},
                                        figure=core.utils.plotly_graphics.empty_sample_variant_figure(),
                                    ),
                                ],
                                style={"position": "relative"},
                            )
                        ],
                        overlay_style={"visibility": "visible", "filter": "blur(1px)"},
                        parent_style={"position": "relative"},
                    ),
                    dcc.Store(
                        id="previous-data",
                        storage_type="memory",
                        data={"first_load": True},
                    ),
                ],
            ),
        ]
    )

    @app.callback(
        [
            Output("needleplot-graph", "figure"),
            Output("samples_markdown", "children"),
            Output("previous-data", "data"),
        ],
        [
            Input("mdata-store", "data"),
            Input("toggle-rangeslider", "value"),
            Input("needleplot-graph", "relayoutData"),
        ],
        State("previous-data", "data"),
    )
    def update_sample(mdata, toggle_rangeslider, relayout_data, prev_data):
        if not mdata or not mdata.get("x"):
            return (
                core.utils.plotly_graphics.empty_sample_variant_figure(),
                "No variants available for the selected sample",
                {"first_load": False},
            )

        previous_data = prev_data or {"first_load": True}
        if (
            not previous_data.get("first_load", True)
            and relayout_data
            and previous_data.get("prev_relayout") == relayout_data
        ):
            raise PreventUpdate

        figure = core.utils.plotly_graphics.build_sample_variant_figure(
            mdata,
            toggle_rangeslider=toggle_rangeslider,
            relayout_data=relayout_data,
        )
        next_data = {
            "first_load": False,
            "prev_relayout": relayout_data,
        }
        return figure, "Showing mutations for selected sample", next_data

