#!/usr/bin/env python3

# Import modules
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash
import dash_core_components as dcc
import dash_html_components as html
from django.conf import settings
from collections import Counter
import plotly.express as px

# import plotly.graph_objects as go
import pandas as pd
import json
import os


def parse_csv(file_path):
    """
    This function loads a CSV file and returns a DataFrame.
    """
    df = pd.read_csv(file_path, sep=",")

    return df


def parse_json_file(json_file):
    """
    This function loads a json file and returns a python dictionary.
    """
    json_parsed = {}
    with open(json_file) as f:
        json_parsed["data"] = json.load(f)

    return json_parsed


def preprocess_json_data_with_csv(json_data, csv_data):
    """
    This function counts the number of samples for each CCAA for a certain lineage.
    """
    lineage_dict = dict()
    for sample_data in json_data["data"]:
        if not csv_data[
            csv_data.SAMPLE == int(sample_data["sequencing_sample_id"])
        ].empty:
            lineage = (
                csv_data[csv_data.SAMPLE == int(sample_data["sequencing_sample_id"])]
                .iloc[0]
                .at["LINEAGE"]
            )
            if lineage_dict.get(lineage) is None:
                lineage_dict[lineage] = [sample_data["geo_loc_state"]]
            else:
                lineage_dict[lineage].append(sample_data["geo_loc_state"])

    lineage_count_dict = dict()
    for lineage in lineage_dict:
        lineage_count_dict[lineage] = dict(Counter(lineage_dict[lineage]))

    # Modify CCAA dictionary to values in JSON file
    ccaa_dict = {
        "Unassigned": 0,
        "Andalucía": 1,
        "Aragón": 2,
        "Islas Baleares": 3,
        "Islas Canarias": 4,
        "Cantabria": 5,
        "Castilla-La Mancha": 6,
        "Castilla y León": 7,
        "Cataluña": 8,
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

    lineage_by_ccaa_df = pd.DataFrame(
        columns=["ID", "CCAA", "Lineage", "Count"]
    ).astype(dtype={"Count": "int32"})

    for lineage in lineage_count_dict:
        for ccaa in lineage_count_dict[lineage]:
            lineage_by_ccaa_df = lineage_by_ccaa_df.append(
                {
                    "ID": ccaa_dict[ccaa],
                    "CCAA": ccaa,
                    "Lineage": lineage,
                    "Count": int(lineage_count_dict[lineage][ccaa]),
                },
                ignore_index=True,
            )
    return lineage_by_ccaa_df


def set_dataframe_geo_plot(df, lineage):
    """
    This function receives a python dictionary, a list of selected fields and sets a dataframe from fields_selected_list
    to represent the graph dataframe structure(dict) { x: [], y: [], domains: [], mutationGroups: [],}
    """
    if lineage is None:
        first_line = df.iloc[0]
        lineage = first_line.at[0, "Lineage"]

    filter_df = df[df.Lineage == lineage]
    print(filter_df)

    return filter_df


def get_list_of_dict_of_lineages_from_long_table(df):
    """
    This function receives parsed file from parse_csv().
    Returns a list of dictionaries of lineages [{"label": "B.1.177.57", "value": "B.1.177.57"}]
    """
    unique_lineages = df.LINEAGE.unique()
    list_of_lineages = []
    for lin in unique_lineages:
        list_of_lineages.append({"label": lin, "value": lin})

    return list_of_lineages


def plot_geomap(lineage):
    # Create a map with lineage frequency by CCAA.

    csv_file = os.path.join(
        settings.BASE_DIR, "relecov_core", "docs", "variants_long_table_last.csv"
    )
    with open(csv_file) as f:
        csv_data = parse_csv(f)
    dict_of_samples = get_list_of_dict_of_lineages_from_long_table(csv_data)

    geojson_file = os.path.join(
        settings.BASE_DIR, "relecov_core", "docs", "spain-communities.geojson"
    )
    # geojson_data = os.path.join(
    #    settings.BASE_DIR, "relecov_core", "docs", "spain-communities.geojson"
    # )

    json_file = os.path.join(
        settings.BASE_DIR,
        "relecov_core",
        "docs",
        "processed_metadata_lab_20220208_20220613.json",
    )
    json_data = parse_json_file(json_file)
    geojson_data = parse_json_file(geojson_file)

    ldata = set_dataframe_geo_plot(
        preprocess_json_data_with_csv(json_data, csv_data), lineage
    )

    print(ldata)

    fig = px.choropleth_mapbox(
        data_frame=ldata,
        geojson=geojson_data,
        locations="ID",
        color=ldata.Count,
        color_continuous_scale="Viridis",
        range_color=(0, ldata.Count.max()),
        mapbox_style="carto-positron",
        zoom=5,
        center={"lat": 35.9, "lon": -5.3},
        opacity=0.5,
        labels={"Count": "Number of samples"},
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    app = DjangoDash("geomap_plot")
    app.layout = html.Div(
        children=[
            "Select a Lineage",
            dcc.Dropdown(
                id="geomap-select-lineage",
                options=dict_of_samples,
                clearable=False,
                multi=False,
                value=lineage,
                # style={"width": "400px"},
            ),
            html.Div(
                children=dcc.Graph(figure=fig, id="geomap-per-lineage"),
            ),
        ],
    )

    @app.callback(
        # Output("geomap-per-lineage", "value"),
        Output("geomap-per-lineage", "figure"),
        Input("geomap-select-lineage", "value"),
    )
    def update_sample(selected_lineage):
        # plot_geomap(selected_lineage)
        lineage_by_ccaa = preprocess_json_data_with_csv(json_data, csv_data)
        ldata = set_dataframe_geo_plot(lineage_by_ccaa, selected_lineage)
        fig = px.choropleth_mapbox(
            data_frame=ldata,
            geojson=geojson_data,
            locations="ID",
            color="Count",
            color_continuous_scale="Viridis",
            range_color=(0, ldata.Count.max()),
            mapbox_style="carto-positron",
            zoom=5,
            center={"lat": 35.9, "lon": -5.3},
            opacity=0.8,
            labels={"Count": "Number of samples"},
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig

    """
def plot_geomap(lineage):
    #Create a map with lineage frequency by CCAA.
    csv_file = os.path.join(
        settings.BASE_DIR, "relecov_core", "docs", "variants_long_table_last.csv"
    )
    with open(csv_file) as f:
        csv_data = parse_csv(f)
    dict_of_samples = get_list_of_dict_of_lineages_from_long_table(csv_data)

    geojson_file = os.path.join(
        settings.BASE_DIR, "relecov_core", "docs", "spain-communities.geojson"
    )

    json_file = os.path.join(
        settings.BASE_DIR,
        "relecov_core",
        "docs",
        "processed_metadata_lab_20220208_20220613.json",
    )
    json_data = parse_json_file(json_file)
    geojson_data= parse_json_file(geojson_file)

    df = set_dataframe_geo_plot(
        preprocess_json_data_with_csv(json_data, csv_data), lineage
    )

    fig = go.Figure(go.Choroplethmapbox(geojson=geojson_data,locations=df.ID,z=df.ID, colorscale="Viridis",zmin=0,zmax=df.Count.max(),marker_opacity=0.5, marker_line_width=0))
    fig.update_layout(mapbox_style="cartro-positron",mapbox_zoom=3, mapbox_center={"lat": 35.9, "lon": -5.3})
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    app = DjangoDash("geomap_plot")
    app.layout = html.Div(
        children=[
            "Select a Lineage",
            dcc.Dropdown(
                id="geomap-select-lineage",
                options=dict_of_samples,
                clearable=False,
                multi=False,
                value=lineage,
                # style={"width": "400px"},
            ),
            html.Div(
                children=dcc.Graph(figure=fig, id="geomap-per-lineage"),
            ),
        ],
    )

    @app.callback(
        # Output("geomap-per-lineage", "value"),
        Output("geomap-per-lineage", "figure"),
        Input("geomap-select-lineage", "value"),
    )
    def update_sample(selected_lineage):
        plot_geomap(selected_lineage)
        lineage_by_ccaa = preprocess_json_data_with_csv(json_data, csv_data)
        ldata = set_dataframe_geo_plot(lineage_by_ccaa, selected_lineage)
        # data_frame = set_dataframe_geo_plot(lineage_by_ccaa, selected_lineage)
        # fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        fig = go.Figure(go.Choroplethmapbox(geojson=geojson_data,locations=df.ID,z=df.ID, colorscale="Viridis",zmin=0,zmax=df.Count.max(),marker_opacity=0.5, marker_line_width=1))
        fig.update_layout(mapbox_style="cartro-positron",mapbox_zoom=3, mapbox_center={"lat": 35.9, "lon": -5.3})
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig
"""
