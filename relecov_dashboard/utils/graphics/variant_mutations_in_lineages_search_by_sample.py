import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
import dash_bio as dashbio

from relecov_core.utils.handling_variant import create_dataframe


def create_needle_plot_graph(sample, mdata):
    app = DjangoDash("needle_plot")

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
                                options=2018185,  # list of dictionaries of samples [{"label": "220685", "value": "220685"}]
                                clearable=False,
                                multi=False,
                                value=sample,
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
                    margin={"t": 100, "l": 20, "r": 400, "b": 40},
                    id="dashbio-needleplot",
                    mutationData=mdata,
                    rangeSlider=False,
                    xlabel="Genome Position",
                    ylabel="Allele Frequency ",
                    domainStyle={
                        "displayMinorDomains": True,
                    },
                ),
            ),
        ]
    )

    @app.callback(
        Output("dashbio-needleplot", "mutationData"),
        Input("needleplot-select-sample", "value"),
    )
    def update_sample(selected_sample):
        mdata = create_dataframe(sample=2018185, organism_code="NC_045512")
        create_needle_plot_graph(selected_sample, mdata=mdata)
        # mutationData = mdata
        # return mutationData

    @app.callback(
        Output("dashbio-needleplot", "rangeSlider"),
        Input("needleplot-rangeslider", "value"),
    )
    def update_range_slider(range_slider_value):
        return True if range_slider_value else False
