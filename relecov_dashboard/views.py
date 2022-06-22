from django.shortcuts import render
from django_plotly_dash import DjangoDash
import plotly.express as px
from dash.dependencies import Input, Output

import json
import urllib.request as urlreq
import dash_bio as dashbio
import dash_html_components as html
import dash_core_components as dcc
from dash_bio.utils import PdbParser, create_mol3d_style
import os
from django.conf import settings
from relecov_core.utils.parse_files import parse_csv_into_list_of_dicts
from .utils.graphic_test import create_test_variant_graph, set_dataframe_range_slider
from relecov_dashboard.utils.graphics.lineages_in_time import parse_json_file


def index(request):
    data_json = os.path.join(
        settings.BASE_DIR, "relecov_core", "docs", "bioinfo_metadata.json"
    )
    mdata = parse_json_file(data_json)
    print(mdata)
    # with open(data_json, "r") as fh:
    #    lines = fh.readlines()
    # for line in lines:
    # mdata = json.loads(data_json)
    #    print(line)
    # mdata=parse_json_file(data_json)
    return render(request, "relecov_dashboard/index.html")


def variants(request):
    variant_data = parse_csv_into_list_of_dicts(
        os.path.join(
            settings.BASE_DIR, "relecov_core", "docs", "variantLuisTableCSV.csv"
        )
    )
    app = DjangoDash(name="TestVariantGraph")
    app.layout = create_test_variant_graph(variant_data, [1, 19])

    @app.callback(Output("graph-with-slider", "figure"), Input("week-slider", "value"))
    def update_figure(selected_range):
        df = set_dataframe_range_slider(variant_data, selected_range)

        fig = px.bar(
            df,
            x="Week",
            y="Sequences",
            color="Variant",
            barmode="stack",
            hover_name="Variant",
        )

        fig.update_layout(transition_duration=500)

        return fig

    return render(request, "relecov_dashboard/variants.html")


def methodology_index(request):
    return render(request, "relecov_dashboard/methodology.html")


def hackaton_group1(request):
    app = DjangoDash("needle_plot")

    data = urlreq.urlopen("https://git.io/needle_PIK3CA.json").read().decode("utf-8")

    mdata = json.loads(data)

    app.layout = html.Div(
        [
            "Show or hide range slider",
            dcc.Dropdown(
                id="default-needleplot-rangeslider",
                options=[{"label": "Show", "value": 1}, {"label": "Hide", "value": 0}],
                clearable=False,
                multi=False,
                value=1,
                style={"width": "400px"},
            ),
            dashbio.NeedlePlot(id="dashbio-default-needleplot", mutationData=mdata),
        ]
    )

    @app.callback(
        Output("dashbio-default-needleplot", "rangeSlider"),
        Input("default-needleplot-rangeslider", "value"),
    )
    def update_needleplot(show_rangeslider):
        return True if show_rangeslider else False

    return render(request, "relecov_dashboard/hackaton_group1.html")


def hackaton_group2(request):
    app = DjangoDash("model3D")

    parser = PdbParser("https://git.io/4K8X.pdb")

    data = parser.mol3d_data()
    styles = create_mol3d_style(
        data["atoms"], visualization_type="cartoon", color_element="residue"
    )

    app.layout = html.Div(
        [
            dashbio.Molecule3dViewer(
                id="dashbio-default-molecule3d", modelData=data, styles=styles
            ),
            "Selection data",
            html.Hr(),
            html.Div(id="default-molecule3d-output"),
        ]
    )

    @app.callback(
        Output("default-molecule3d-output", "children"),
        Input("dashbio-default-molecule3d", "selectedAtomIds"),
    )
    def show_selected_atoms(atom_ids):
        if atom_ids is None or len(atom_ids) == 0:
            return "No atom has been selected. Click somewhere on the molecular \
            structure to select an atom."
        return [
            html.Div(
                [
                    html.Div("Element: {}".format(data["atoms"][atm]["elem"])),
                    html.Div("Chain: {}".format(data["atoms"][atm]["chain"])),
                    html.Div(
                        "Residue name: {}".format(data["atoms"][atm]["residue_name"])
                    ),
                    html.Br(),
                ]
            )
            for atm in atom_ids
        ]

    return render(request, "relecov_dashboard/hackaton_group2.html")


def hackaton_group3(request):
    return render(request, "relecov_dashboard/hackaton_group3.html")


def hackaton_group4(request):
    return render(request, "relecov_dashboard/hackaton_group4.html")
