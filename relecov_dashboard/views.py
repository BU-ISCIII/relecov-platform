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
from relecov_dashboard.utils.graphics.lineages_in_time_graph import (
    create_test_variant_graph,
    set_dataframe_range_slider,
)

"""
from relecov_dashboard.utils.graphics.needle_plot_graph import (
    parse_json_file,
    # get_list_of_keys,
    # parse_csv,
    # set_dataframe_needle_plot,
)
"""


def dashboard(request):
    # PARSE JSON
    # data_json = os.path.join(
    #    settings.BASE_DIR, "relecov_core", "docs", "bioinfo_metadata.json"
    # )
    # json_data = parse_json_file(data_json)
    # list_keys = get_list_of_keys(json_data)
    # print(list_keys)

    return render(request, "relecov_dashboard/dashboard.html")


def lineages_in_time(request):
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

    return render(request, "relecov_dashboard/lineages_in_time.html")


def methodology_index(request):
    return render(request, "relecov_dashboard/methodology.html")


def needle_plot(request):
    # PARSE CSV
    # data_long_table = os.path.join(
    # settings.BASE_DIR,"relecov_core","docs","variants_long_table_last.csv"
    # )
    # csv_data= parse_csv(data_long_table)
    # df = set_dataframe_needle_plot(csv_data)

    app = DjangoDash("needle_plot")

    data = urlreq.urlopen("https://git.io/needle_PIK3CA.json").read().decode("utf-8")

    mdata = json.loads(data)
    # mdata = df

    app.layout = html.Div(
        children=[
            "Show or hide range slider",
            dcc.Dropdown(
                id="default-needleplot-rangeslider",
                options=[{"label": "Show", "value": 1}, {"label": "Hide", "value": 0}],
                clearable=False,
                multi=False,
                value=0,
                style={"width": "400px"},
            ),
            html.Div(
                children=dashbio.NeedlePlot(
                    width="auto", id="dashbio-default-needleplot", mutationData=mdata
                ),
            ),
        ],
    )

    @app.callback(
        Output("dashbio-default-needleplot", "rangeSlider"),
        Input("default-needleplot-rangeslider", "value"),
    )
    def update_needleplot(show_rangeslider):
        return True if show_rangeslider else False

    return render(request, "relecov_dashboard/needle_plot.html")


def molecular_3D(request):
    app = DjangoDash("model3D")

    parser = PdbParser("https://git.io/4K8X.pdb")

    data = parser.mol3d_data()
    styles = create_mol3d_style(
        data["atoms"], visualization_type="cartoon", color_element="residue"
    )

    app.layout = html.Div(
        [
            dashbio.Molecule3dViewer(
                width="1200",
                id="dashbio-default-molecule3d",
                modelData=data,
                styles=styles,
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

    return render(request, "relecov_dashboard/molecular_3D.html")


def hackaton_group1(request):
    return render(request, "relecov_dashboard/hackaton_group1.html")


def hackaton_group2(request):
    return render(request, "relecov_dashboard/hackaton_group2.html")


def hackaton_group3(request):
    return render(request, "relecov_dashboard/hackaton_group3.html")


def hackaton_group4(request):
    return render(request, "relecov_dashboard/hackaton_group4.html")
