## Generic imports
#import os
#import json
#import plotly.express as px
#from dash import dcc, html
#from django_plotly_dash import DjangoDash
#
## Local imports
#from relecov_platform import settings as relecov_platform_settings
#import dashboard.models
#
#
#def create_samples_received_map():
#    geojson_file = os.path.join(
#        relecov_platform_settings.STATIC_ROOT,
#        "dashboard",
#        "custom",
#        "map",
#        "spain-communities.geojson",
#    )
#    with open(geojson_file, encoding="utf-8") as geo_json:
#        counties = json.load(geo_json)
#    json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
#        "received_samples_map"
#    )
#    if json_data is None:
#        # Execute the pre-processed task to get the data
#        result = dashboard.utils.generic_process_data.pre_proc_samples_received_map()
#        if "ERROR" in result:
#            return result
#        json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
#            "received_samples_map"
#        )
#
#    fig = px.choropleth_mapbox(
#        json_data,
#        geojson=counties,
#        locations=json_data["ccaa_id"],
#        color=json_data["ccaa_id"],
#        color_continuous_scale="Viridis",
#        mapbox_style="carto-positron",
#        zoom=3.8,
#        center={"lat": 35.9, "lon": -5.3},
#        opacity=0.5,
#        labels={
#            "ccaa_name": "CCAA",
#            "samples": "SAMPLES",
#        },
#        custom_data=[
#            "samples",
#        ],
#        hover_name="ccaa_name",
#        hover_data={"ccaa_id": False, "samples": True},
#    )
#    fig.update_layout(
#        coloraxis_showscale=False, margin={"r": 0, "t": 30, "l": 0, "b": 0}
#    )
#    # Don't show legend in plotly.express
#    fig.update_traces(
#        showlegend=False,
#        hovertemplate="<b>%{hovertext}</b><br>Samples: %{customdata[0]}",
#    )
#    app = DjangoDash("samplesReceivedOverTimeMap")
#    app.layout = html.Div(
#        children=[
#            dcc.Graph(className="card", id="geomap-per-lineage", figure=fig),
#        ],
#    )
#

# Generic imports
import os
import json
import folium
from dash import html
from django_plotly_dash import DjangoDash
import pandas as pd

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

    
    samples_df = pd.DataFrame(json_data)
    samples_df["id"] = samples_df["ccaa_id"].astype(str)
    samples_df["samples"] = pd.to_numeric(samples_df["samples"], errors="coerce").fillna(0)

    
    samples_dict = samples_df.set_index("id")["samples"].to_dict()
    for feature in counties["features"]:
        ccaa_id = str(feature["properties"]["cartodb_id"])
        feature["properties"]["samples"] = samples_dict.get(ccaa_id, 0)

    
    m = folium.Map(location=[40, -3.7], zoom_start=5, tiles=None)
    
    folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
    attr='Tiles &copy; Esri &mdash; Source: USGS, Esri, TANA, DeLorme, and NPS',
    name="Esri World Terrain",
    max_zoom=13
    ).add_to(m)

    folium.Choropleth(
        geo_data=counties,
        data=samples_df,
        columns=["id", "samples"],
        key_on="properties.cartodb_id",
        fill_color="BuGn",
        fill_opacity=0.7,
        line_opacity=0.2,
        highlight=True,
        legend_name="Muestras Recibidas"
    ).add_to(m)

    folium.GeoJson(
        counties,
        name="Comunidades Autónomas",
        style_function=lambda feature: {
            "fillColor": "transparent",
            "color": "black",
            "weight": 1,
        },
        highlight_function= lambda feature: {
            "fillColor": "ffff00",
            "color": "transparent",
            "weight": "3",
            "dashArray": "5, 5"
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "samples"],
            aliases=["CCAA:", "Muestras:"],
            localize=True,
            sticky=False,
            labels=True,
            style="background-color: white; color: black; font-weight: bold;",
        )
    ).add_to(m)
    
    m.get_root().html.add_child(folium.Element("""
    <style>
        .leaflet-interactive:focus { outline: none !important; box-shadow: none !important; }
    </style>
    """))

    # Generar el HTML del mapa
    map_html = m.get_root().render()

    # Reemplazar el gráfico de Plotly por Folium en DjangoDash
    app = DjangoDash("samplesReceivedOverTimeMap")
    app.layout = html.Div(
        children=[
            html.Iframe(srcDoc=map_html, style={"width": "100%", "height": "800px"}),
        ],
    )
