# Generic imports
import os
import json
import plotly.express as px
from dash import dcc, html
from django_plotly_dash import DjangoDash

# Local imports
from relecov_platform import settings as relecov_platform_settings
import dashboard.models


def create_samples_received_map():
    geojson_file = os.path.join(
        relecov_platform_settings.STATIC_ROOT,
        "dashboard",
        "custom",
        "map",
        "spain-communities.geojson",
    )
    with open(geojson_file, encoding="utf-8") as geo_json:
        counties = json.load(geo_json)
    json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
        "received_samples_map"
    )
    if json_data is None:
        # Execute the pre-processed task to get the data
        result = dashboard.utils.generic_process_data.pre_proc_samples_received_map()
        if "ERROR" in result:
            return result
        json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
            "received_samples_map"
        )

    fig = px.choropleth_mapbox(
        json_data,
        geojson=counties,
        locations=json_data["ccaa_id"],
        color=json_data["ccaa_id"],
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        zoom=3.8,
        center={"lat": 35.9, "lon": -5.3},
        opacity=0.5,
        labels={
            "ccaa_name": "CCAA",
            "samples": "SAMPLES",
        },
        custom_data=[
            "samples",
        ],
        hover_name="ccaa_name",
        hover_data={"ccaa_id": False, "samples": True},
    )
    fig.update_layout(coloraxis_showscale=False, margin={"r": 0, "t": 30, "l": 0, "b": 0})
    # Don't show legend in plotly.express
    fig.update_traces(
        showlegend=False,
        hovertemplate="<b>%{hovertext}</b><br>Samples: %{customdata[0]}"
    )
    app = DjangoDash("samplesReceivedOverTimeMap")
    app.layout = html.Div(
        children=[
            dcc.Graph(className="card", id="geomap-per-lineage", figure=fig),
        ],
    )
