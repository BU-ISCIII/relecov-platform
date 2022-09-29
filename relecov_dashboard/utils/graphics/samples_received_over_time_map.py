import os
import pandas as pd
import json
import plotly.express as px

import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash

# sfrom dash.dependencies import Input, Output
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
        # color=ldata.CCAA_NAME,
        color_continuous_scale="Viridis",
        range_color=ldata.NUMBER_OF_SAMPLES.max(),
        mapbox_style="carto-positron",
        zoom=3.5,
        center={"lat": 35.9, "lon": -5.3},
        opacity=0.5,
        # labels={"CCAA": ldata.CCAA_NAME},
        labels={
            "CCAA_ID": "CCAA ID",
            "CCAA_NAME": "CCAA NAME",
            "NUMBER_OF_SAMPLES": "NUMBER OF SAMPLES PER CCAA",
        },
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    app = DjangoDash("samplesReceivedOverTimeMap")
    app.layout = html.Div(
        children=[
            html.Br(),
            "Number of sample received in Spain per CCAA",
            html.Br(),
            html.Br(),
            html.Div(
                children=dcc.Graph(figure=fig, id="geomap-per-lineage"),
            ),
        ],
    )
    """
    ccaa_dict = {
        "Unassigned": 0,
        "Andalucía": 1,
        "Aragón": 2,
        "Islas Baleares": 3,
        "Islas Canarias": 4,
        "Cantabria": 5,
        "Castilla-La Mancha": 6,
        "Castilla y León": 7,
        # "Cataluña": 8,
        "Catalonia": 8,
        "Ceuta": 9,
        "Extremadura": 10,
        "Galicia": 11,
        "La Rioja": 12,
        "Madrid": 13,
        "Melilla": 14,
        "Murcia": 15,
        "Navarra": 16,
        "País Vasco": 17,
        "Asturias": 18,
        "Comunidad Valenciana": 19,
    }
    """

    """
    @app.callback(
        Output("geomap-per-lineage", "figure"),
        Input("geomap-select-lineage", "value"),
    )
    def update_sample(selected_lineage):
        # lineage_by_ccaa = preprocess_json_data_with_csv(json_data, csv_data)
        # ldata = set_dataframe_geo_plot(lineage_by_ccaa, selected_lineage)
        ldata = parse_json_file()
        fig = px.choropleth_mapbox(
            data_frame=ldata,
            geojson=counties,
            locations=ldata.CCAA_ID,
            color=ldata.NUMBER_OF_SAMPLES,
            color_continuous_scale="Viridis",
            range_color=ldata.NUMBER_OF_SAMPLES.max(),
            mapbox_style="carto-positron",
            zoom=5,
            center={"lat": 35.9, "lon": -5.3},
            opacity=0.5,
            #labels={"Count": "Number of samples"},
            labels={"CCAA_NAME": "CCAA NAME"},
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig
    """
