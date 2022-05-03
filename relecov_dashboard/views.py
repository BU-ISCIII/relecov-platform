# from unicodedata import name
from django.shortcuts import render

# from plotly.offline import plot
# import plotly.graph_objects as go

# plotly dash
# import dash_core_components as dcc
# import dash_html_components as html
from django_plotly_dash import DjangoDash

# import plotly.graph_objects as go
import plotly.express as px

# import pandas as pd

# from dash import Input, Output#Dash, dcc, html,
from dash.dependencies import Input, Output

# import dash
import os
from django.conf import settings

# import dash_bootstrap_components as dbc

# IMPORT FROM UTILS

from relecov_core.utils.parse_files import parse_csv_into_list_of_dicts

# from relecov_core.utils.dashboard import *
from .utils.graphic_test import create_test_variant_graph, set_dataframe_range_slider


def index(request):
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

    return render(request, "relecov_dashboard/index.html")


def methodology_index(request):
    return render(request, "relecov_dashboard/methodology.html")
