import json
import os

import folium
import pandas as pd

# Local imports
import dashboard.utils.generic_graphic_data
import dashboard.utils.generic_process_data
from relecov_platform import settings as relecov_platform_settings


def build_samples_received_map_html():
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
    samples_df["samples"] = pd.to_numeric(
        samples_df["samples"], errors="coerce"
    ).fillna(0)

    samples_dict = samples_df.set_index("id")["samples"].to_dict()
    for feature in counties["features"]:
        ccaa_id = str(feature["properties"]["cartodb_id"])
        feature["properties"]["samples"] = samples_dict.get(ccaa_id, 0)

    m = folium.Map(location=[40, -3.7], zoom_start=5, tiles=None)

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: USGS, Esri, TANA, DeLorme, and NPS",
        name="Esri World Terrain",
        max_zoom=13,
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
        legend_name="Muestras Recibidas",
    ).add_to(m)

    folium.GeoJson(
        counties,
        name="Comunidades Autónomas",
        style_function=lambda feature: {
            "fillColor": "transparent",
            "color": "black",
            "weight": 1,
        },
        highlight_function=lambda feature: {
            "fillColor": "ffff00",
            "color": "transparent",
            "weight": "3",
            "dashArray": "5, 5",
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "samples"],
            aliases=["CCAA:", "Muestras:"],
            localize=True,
            sticky=False,
            labels=True,
            style="background-color: white; color: black; font-weight: bold;",
        ),
    ).add_to(m)

    m.get_root().html.add_child(folium.Element("""
    <style>
        .leaflet-interactive:focus { outline: none !important; box-shadow: none !important; }
    </style>
    """))

    return m.get_root().render()


def create_samples_received_map():
    result = build_samples_received_map_html()
    if isinstance(result, dict) and "ERROR" in result:
        return result
    return {"OK": True}
