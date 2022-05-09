from django.shortcuts import render
from django_plotly_dash import DjangoDash
import plotly.express as px
from dash.dependencies import Input, Output
import os
from django.conf import settings
from relecov_core.utils.parse_files import parse_csv_into_list_of_dicts
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
