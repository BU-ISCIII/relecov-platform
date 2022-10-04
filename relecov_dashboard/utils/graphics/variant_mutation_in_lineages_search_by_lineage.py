import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
import dash_bio as dashbio
from relecov_core.utils.handling_variant import get_variant_data_from_lineages


def create_needle_plot_graph_mutation_by_lineage(lineage, mdata):
    app = DjangoDash("needlePlotMutationByLineage")

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
                            "Select a Lineage",
                            dcc.Dropdown(
                                id="needleplot-select-lineage",
                                options=[
                                    {"label": "B.1.1.7", "value": "B.1.1.7"}
                                ],  # dict_of_samples,
                                clearable=False,
                                multi=False,
                                value=lineage,
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
                    id="dashbio-needleplot",
                    xlabel="Genome Position",
                    ylabel="Allele Frequency ",
                    mutationData=mdata,
                    rangeSlider=True,
                    domainStyle={
                        # "textangle": "45",
                        "displayMinorDomains": True,
                        "domainColor": [
                            "#FFDD00",
                            "#00FFDD",
                            "#0F0F0F",
                            "#D3D3D3",
                            "#FFDD00",
                            "#00FFDD",
                            "#0F0F0F",
                            "#D3D3D3",
                            "#FFDD00",
                            "#00FFDD",
                            "#0F0F0F",
                        ],
                    },
                    needleStyle={
                        "stemColor": "#444",
                        "stemThickness": 0.5,
                        "stemConstHeight": False,
                        "headSize": 5,
                        "headColor": [
                            "#e41a1c",
                            "#377eb8",
                            "#4daf4a",
                            "#984ea3",
                            "#ff7f00",
                            "#ffff33",
                            "#a65628",
                            "#f781bf",
                            "#999999",
                            "#e41a1c",
                            "#377eb8",
                            "#4daf4a",
                            "#984ea3",
                            "#ff7f00",
                            "#ffff33",
                            "#a65628",
                            "#f781bf",
                            "#999999",
                            "#e41a1c",
                        ],
                        "headSymbol": "circle",
                    },
                ),
            ),
        ]
    )

    @app.callback(
        Output("dashbio-needleplot", "mutationData"),
        Input("needleplot-select-lineage", "value"),
    )
    def update_sample(selected_lineage):
        mdata = get_variant_data_from_lineages("B.1.1.7", "NC_045512")
        create_needle_plot_graph_mutation_by_lineage(selected_lineage, mdata)
        # mutation_data = mdata
        # return mutation_data

    @app.callback(
        Output("dashbio-needleplot", "rangeSlider"),
        Input("needleplot-rangeslider", "value"),
    )
    def update_range_slider(range_slider_value):
        return True if range_slider_value else False
