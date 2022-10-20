import os
import pandas as pd
import json
import plotly.express as px

import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash

from relecov_platform import settings


def parse_json_file():
    """
    This function loads a json file and returns a python dictionary.
    """

    list_of_ccaa_id = []
    list_of_number_of_samples = []
    list_of_lists = []
    input_file = os.path.join(
        settings.BASE_DIR,
        "relecov_core",
        "docs",
        "data_for_geomap_from_ISkyLims_only_region.json",
    )
    with open(input_file) as f:
        data = json.load(f)

    region_data = data["region"]
    list_of_ccaa_id = region_data.keys()
    list_of_number_of_samples = region_data.values()
    list_of_ccaa_name = [
        "Andalucia",
        "Aragón",
        "Asturias",
        "Islas Baleares",
        "Islas Canarias",
        "Murcia",
        "Castilla-La Mancha",
        "Galicia",
        "Madrid",
        "Navarra",
        "Catalonia",
        "Castilla y León",
        "Extremadura",
        "Cantabria",
        "Comunidad Valenciana",
        "Ceuta",
        "Melilla",
        "País Vasco",
        "La Rioja",
    ]

    list_of_lists.append(list_of_ccaa_id)
    list_of_lists.append(list_of_ccaa_name)
    list_of_lists.append(list_of_number_of_samples)

    df = pd.DataFrame(list_of_lists).transpose()
    df.columns = ["CCAA_ID", "CCAA_NAME", "NUMBER_OF_SAMPLES"]
    df = df.sort_values(by=["NUMBER_OF_SAMPLES"])

    return df


def create_samples_received_over_time_map():
    ldata = parse_json_file()

    geojson_file = os.path.join(
        settings.BASE_DIR, "relecov_core", "docs", "spain-communities.geojson"
    )

    with open(geojson_file) as geo_json:
        counties = json.load(geo_json)
    
    fig = px.choropleth_mapbox(
        ldata,
        geojson=counties,
        locations=ldata.CCAA_ID,
        color=ldata.NUMBER_OF_SAMPLES,
        color_continuous_scale="Viridis",
        range_color=ldata.CCAA_NAME,
        mapbox_style="carto-positron",
        zoom=3.8,
        center={"lat": 35.9, "lon": -5.3},
        opacity=0.5,
        labels={
            "CCAA_ID": "ID",
            "CCAA_NAME": "CCAA",
            "NUMBER_OF_SAMPLES": "NUMBER OF SAMPLES",
        },
        custom_data=[
            "NUMBER_OF_SAMPLES",
        ],
        hover_name="CCAA_NAME",
        hover_data = {'CCAA_ID':False},
    )
    fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})
    # Don't show legend in plotly.express
    fig.update_traces(showlegend=False)
    
    app = DjangoDash("samplesReceivedOverTimeMap")
    app.layout = html.Div(
        className="card",
        children=[
            html.Div(
                className="card-body bg-dark",
                children=[
                    html.H1(
                        className="card-title",
                        children="Samples in Spain",
                    ),
                    html.Div(
                        className="card-text",
                        children="Number of sample received in Spain per CCAA.",
                    ),
                ],
            ),
            html.Br(),
            html.Div(
                children=[
                    html.Div(
                        children=[
                            dcc.Graph(
                                className="card", id="geomap-per-lineage", figure=fig
                            )
                        ]
                    )
                ]
            ),
        ],
    )
    