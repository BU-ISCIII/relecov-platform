import json
import os
from django.conf import settings

import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
import dash_bio as dashbio


def parse_csv(file_path):
    """
    fields => SAMPLE(0), CHROM(1), POS(2), REF(3), ALT(4),
    FILTER(5), DP(6),  REF_DP(7), ALT_DP(8), AF(9), GENE(10),
    EFFECT(11), HGVS_C(12), HGVS_P(13), HGVS_P1LETTER(14),
    CALLER(15), LINEAGE(16)
    """

    with open(file_path) as fh:
        lines = fh.readlines()

    return lines


def set_dataframe_needle_plot(lines_from_long_table, sample):
    """
    This function receives a python dictionary, a list of selected fields and sets a dataframe from fields_selected_list to represent the graph
    dataframe structure(dict) { x: [], y: [], domains: [], mutationGroups: [],}
    """
    pos_list = []
    af_list = []
    effect_list = []
    gene_list = []
    if sample is None:
        first_line = lines_from_long_table[1].split(",")
        sample = first_line[0]
    df = {}

    for line in lines_from_long_table[1:]:
        data_array = line.split(",")
        if data_array[0] == sample:
            pos_list.append(data_array[2])
            af_list.append(data_array[9])
            effect_list.append(data_array[11])
            gene_list.append(data_array[10])

    df["x"] = pos_list
    df["y"] = af_list
    df["mutationGroups"] = effect_list
    df["domains"] = [
        {"name": "orf1a", "coord": "265-13468"},
        {"name": "orf1b", "coord": "13468-21555"},
        {"name": "Spike", "coord": "21563-25384"},
        {"name": "orf3a", "coord": "25393-26220"},
        {"name": "E", "coord": "26245-26472"},
        {"name": "M", "coord": "26523-27191"},
        {"name": "orf6", "coord": "27202-27387"},
        {"name": "orf7a", "coord": "27394-27759"},
        {"name": "orf8", "coord": "27894-28259"},
        {"name": "N", "coord": "28274-29533"},
        {"name": "orf10", "coord": "29558-29674"},
    ]
    """
    {"name": "orf1a", "coord": "265-13468"},
    {"name": "orf1b", "coord": "13468-21555"},
    {"name": "Spike", "coord": "21563-25384"},
    {"name": "orf3a", "coord": "25393-26220"},
    {"name": "E", "coord": "26245-26472"},
    {"name": "M", "coord": "26523-27191"},
    {"name": "orf6", "coord": "27202-27387"},
    {"name": "orf7a", "coord": "27394-27759"},
    {"name": "orf8", "coord": "27894-28259"},
    {"name": "N", "coord": "28274-29533"},
    {"name": "orf10", "coord": "29558-29674"}
    """

    return df


def parse_json_file(json_file):
    """
    This function loads a json file and returns a python dictionary.
    """
    json_parsed = {}
    # f = open(json_file)
    with open(json_file) as f:
        json_parsed["data"] = json.load(f)

    return json_parsed


def get_list_of_keys(json_parsed):
    list_of_keys = list(json_parsed["data"].keys())
    return list_of_keys


def get_list_of_dict_of_samples_from_long_table(lines):
    """
    This function receives parsed file from parse_csv().
    Returns a a list of dictionaries of samples [{"label": "220685", "value": "220685"}]
    """

    list_of_samples = []
    for line in lines[1:]:
        dict_of_samples = {}
        data_array = line.split(",")
        if (
            len(list_of_samples) == 0
            or {"label": data_array[0], "value": data_array[0]} not in list_of_samples
        ):
            dict_of_samples["label"] = data_array[0]
            dict_of_samples["value"] = data_array[0]
            list_of_samples.append(dict_of_samples)

    return list_of_samples


def create_needle_plot_graph(sample):
    needle_data = os.path.join(
        settings.BASE_DIR, "relecov_core", "docs", "variants_long_table_last.csv"
    )
    dict_of_samples = get_list_of_dict_of_samples_from_long_table(
        parse_csv(needle_data)
    )
    mdata = set_dataframe_needle_plot(parse_csv(needle_data), sample)
    print(mdata)

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
                                options=dict_of_samples,
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
                    # height="auto",
                    margin={"t": 100, "l": 20, "r": 400, "b": 40},
                    # clickData=["265","29674"],
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
        create_needle_plot_graph(selected_sample)
        mdata = set_dataframe_needle_plot(parse_csv(needle_data), selected_sample)
        mutationData = mdata
        return mutationData

    @app.callback(
        Output("dashbio-needleplot", "rangeSlider"),
        Input("needleplot-rangeslider", "value"),
    )
    def update_range_slider(range_slider_value):
        return True if range_slider_value else False
