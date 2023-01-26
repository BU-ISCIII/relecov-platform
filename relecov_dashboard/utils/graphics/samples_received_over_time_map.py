import os
import pandas as pd
import json
import plotly.express as px

from dash import dcc, html
from django_plotly_dash import DjangoDash

from relecov_platform import settings
from relecov_core.utils.rest_api_handling import get_summarize_data


def create_samples_received_over_time_map():

    geojson_file = os.path.join(
        settings.STATIC_ROOT, "relecov_dashboard", "custom", "map", "spain-communities.geojson"
    )
    raw_data = get_summarize_data("")
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
        className="card",
        children=[
            html.Div(
                className="card-body",
            ),
            dcc.Graph(className="card", id="geomap-per-lineage", figure=fig),
        ],
    )
