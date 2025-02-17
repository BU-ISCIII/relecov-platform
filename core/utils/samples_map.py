# Generic imports
import os
import json
import pandas as pd
import plotly.express as px
from dash import dcc, html
from django_plotly_dash import DjangoDash

# Local imports
from relecov_platform import settings as relecov_platform_settings
import core.utils.rest_api


def create_samples_received_map():
    geojson_file = os.path.join(
        relecov_platform_settings.STATIC_ROOT,
        "dashboard",
        "custom",
        "map",
        "spain-communities.geojson",
    )
    raw_data = core.utils.rest_api.get_summarize_data("")
    if "ERROR" in raw_data:
        return raw_data

    with open(geojson_file, encoding="utf-8") as geo_json:
        counties = json.load(geo_json)

    data = {"ccaa_id": [], "ccaa_name": [], "samples": []}
    for region in counties["features"]:
        ccaa_name = region["properties"]["name"]
        data["ccaa_id"].append(region["properties"]["cartodb_id"])
        data["ccaa_name"].append(ccaa_name)
        if ccaa_name in raw_data["region"]:
            data["samples"].append(raw_data["region"][ccaa_name])
        else:
            data["samples"].append("0")
    ldata = pd.DataFrame(data)

    fig = px.choropleth_mapbox(
        ldata,
        geojson=counties,
        locations=ldata.ccaa_id,
        color=ldata.samples,
        color_continuous_scale="Viridis",
        range_color=ldata.ccaa_name,
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
        hover_data={"ccaa_id": False},
    )
    fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})
    # Don't show legend in plotly.express
    fig.update_traces(showlegend=False)
    app = DjangoDash("samplesReceivedOverTimeMap")
    app.layout = html.Div(
        children=[
            dcc.Graph(className="card", id="geomap-per-lineage", figure=fig),
        ],
    )
