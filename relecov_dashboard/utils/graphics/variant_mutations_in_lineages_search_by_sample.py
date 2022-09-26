import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
import dash_bio as dashbio

from relecov_core.utils.handling_variant import create_dataframe


def create_needle_plot_graph(sample_name, mdata):
    sample_list = [2018185, 210067]
    app = DjangoDash("needle_plot_by_sample")

    app.layout = html.Div(
        children=[
            html.Div(
                children=[
                    html.Div(
                        children=[
                            "Show or hide range slider",
                            dcc.Dropdown(
                                id="needleplot-rangeslider",
                                options=[
                                    {"label": "Show", "value": 1},
                                    {"label": "Hide", "value": 0},
                                ],
                                clearable=False,
                                multi=False,
                                value=1,
                                style={"width": "150px", "margin-right": "30px"},
                            ),
                        ]
                    ),
                    html.Div(
                        children=[
                            "Select a Sample",
                            dcc.Dropdown(
                                id="needleplot-select-sample",
                                options=[{"label": i, "value": i} for i in sample_list],
                                clearable=False,
                                multi=False,
                                value=sample_list[0],
                                style={"width": "150px"},
                            ),
                        ]
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "start",
                    "align-items": "flex-start",
                },
            ),
            html.Div(
                children=dashbio.NeedlePlot(
                    width="auto",
                    # margin={"t": 100, "l": 20, "r": 400, "b": 40},
                    id="dashbio-needleplot",
                    mutationData=mdata,
                    rangeSlider=True,
                    xlabel="Genome Position",
                    ylabel="Allele Frequency ",
                    domainStyle={
                        # "displayMinorDomains": False,
                        "textangle": 90,
                    },
                ),
            ),
        ]
    )

    @app.callback(
        Output("dashbio-needleplot", "mutationData"),
        Input("needleplot-select-sample", "value"),
    )
    def update_sample(selected_sample: int):
        mdata = create_dataframe(sample_name=selected_sample, organism_code="NC_045512")
        mutationData = mdata
        return mutationData

    @app.callback(
        Output("dashbio-needleplot", "rangeSlider"),
        Input("needleplot-rangeslider", "value"),
    )
    def update_range_slider(range_slider_value):
        return True if range_slider_value else False
