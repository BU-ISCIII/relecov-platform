# Generic imports
import dash_bio as dashbio
from dash import dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

# Local imports
import dashboard.utils.generic_graphic_data
import dashboard.utils.generic_process_data


def get_variant_data_from_lineages(graphic_name=None, lineage=None, chromosome=None):
    json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(graphic_name)

    if json_data is None:
        # Execute the pre-processed task to get the data
        result = dashboard.utils.generic_process_data.pre_proc_variations_per_lineage(
            chromosome
        )
        if "ERROR" in result:
            return result

    json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(graphic_name)
    # Return None to indicate that there is no data stored yet
    if json_data is None:
        return None, None, None

    if lineage is None:
        lineage = sorted(list(json_data.keys()))[0]
    mdata = json_data[lineage]
    n_samples = mdata["SamplesWithLineage"]

    return mdata, lineage, n_samples


def create_needle_plot_graph_mutation_by_lineage(
    lineage_list, lineage, mdata, n_samples
):
    options = []
    for lin in lineage_list:
        options.append({"label": lin, "value": lin})

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
                        ],
                    ),
                    html.Div(
                        children=[
                            "Select Lineage",
                            dcc.Dropdown(
                                id="needleplot-select-lineage",
                                options=options,
                                clearable=False,
                                multi=False,
                                value=lineage,
                                style={"width": "150px", "margin-right": "30px"},
                            ),
                        ],
                        style={"margin-left": "20px"},
                    ),
                    html.Div(
                        children=[
                            dcc.Markdown(
                                id="samples_markdown",
                                children=f"Showing mutations for {n_samples} samples",
                            )
                        ],
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
                children=dashbio.NeedlePlot(
                    width="auto",
                    id="dashbio-needleplot",
                    mutationData=mdata,
                    rangeSlider=True,
                    xlabel="Genome Position",
                    ylabel="Population Allele Frequency",
                    domainStyle={
                        # "textangle": "45",
                        "displayMinorDomains": False,
                    },
                ),
            ),
        ]
    )

    @app.callback(
        Output("dashbio-needleplot", "mutationData"),
        Output("dashbio-needleplot", "lineage"),
        Output("samples_markdown", "children"),
        Input("needleplot-select-lineage", "value"),
    )
    def update_sample(selected_lineage):
        mdata, lineage, n_samples = get_variant_data_from_lineages(
            graphic_name="variations_per_lineage",
            lineage=selected_lineage,
            chromosome=None,
        )
        markdown_text = f"Showing mutations for {n_samples} samples"
        return mdata, lineage, markdown_text

    @app.callback(
        Output("dashbio-needleplot", "rangeSlider"),
        Input("needleplot-rangeslider", "value"),
    )
    def update_range_slider(range_slider_value):
        return True if range_slider_value else False
