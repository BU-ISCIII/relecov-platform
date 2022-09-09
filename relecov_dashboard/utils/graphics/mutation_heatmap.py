"""
Mutation heatmap

- Read mutation data
- Process data
- Create plotly heatmap:
    - Rows are samples
    - Mutations are columns
    - Color represents allele frequency

"""
import os
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

import pandas as pd


from relecov_dashboard.utils.graphics.mutation_table import (
    read_mutation_data,
    process_mutation_df,
)
from relecov_platform import settings


def get_figure(data: pd.DataFrame, sample_ids: list, genes: list = None):
    # Filter
    filter = {"SAMPLE": sample_ids, "GENE": genes}
    for col, filter in filter.items():
        if filter and type(filter) == list:
            data = data[data[col].isin(filter)]

    # Order by position
    data = data.sort_values(by=["POS"])

    # Add gene name and mutation into one column
    data["G_MUT"] = data["GENE"] + " - " + data["MUTATION"]

    # Pivot table
    pivot_df = pd.pivot_table(
        data, values="AF", index=["SAMPLE"], columns=["G_MUT"], fill_value=None
    )

    # Order
    pivot_df = pivot_df.sort_index()
    pivot_df.index = pivot_df.index.astype(str)

    # Heatmap
    fig = px.imshow(
        pivot_df,
        aspect="auto",
        labels=dict(x="Mutation", y="Sample", color="AF"),
        color_continuous_scale="RdYlGn",
        range_color=[0, 1],
    )
    fig.update(layout_coloraxis_showscale=True, layout_showlegend=False)
    fig.update_layout(
        yaxis={"title": "Samples"},
        xaxis={"title": "Mutations", "tickangle": 45},
        yaxis_nticks=len(pivot_df) if len(pivot_df) <= 50 else 50,
        xaxis_nticks=len(pivot_df.columns) if len(pivot_df.columns) <= 100 else 100,
    )
    fig.update_traces(xgap=1)

    return fig


def create_hot_map():
    input_file = os.path.join(
        settings.BASE_DIR, "relecov_core", "docs", "variants_long_table_last.csv"
    )
    sample_ids = [214821, 220685, 214826, 214825]
    df = read_mutation_data(input_file, file_extension="csv")
    df = process_mutation_df(df)

    all_genes = list(df["GENE"].unique())
    all_sample_ids = list(df["SAMPLE"].unique())

    app = DjangoDash("mutation_heatmap")

    app.layout = html.Div(
        children=[
            html.Div(
                style={
                    "display": "flex",
                    "justify-content": "start",
                    "align-items": "flex-start",
                },
                children=[
                    dcc.Dropdown(
                        id="mutation_heatmap-select_sample",
                        options=[{"label": i, "value": i} for i in all_sample_ids],
                        clearable=False,
                        multi=True,
                        value=sample_ids,
                        style={"width": "500px", "margin-right": "30px"},
                    ),
                    dcc.Dropdown(
                        id="mutation_heatmap-gene_dropdown",
                        options=[{"label": i, "value": i} for i in all_genes],
                        clearable=False,
                        multi=True,
                        value=None,
                        style={"width": "400px", "margin-right": "30px"},
                        placeholder="Filter genes",
                    ),
                ],
            ),
            dcc.Graph(
                id="mutation_heatmap",
                figure=get_figure(df, sample_ids),
                style={"width": "1500px", "height": "700px"},
            ),
        ]
    )

    def update_selected_sample(data: pd.DataFrame, selected_sample: int):
        if selected_sample and type(selected_sample) == int:
            data = data[data["SAMPLE"].isin([selected_sample])]
        return data

    def update_selected_genes(data: pd.DataFrame, selected_genes: int):
        if selected_genes and type(selected_genes) == list and len(selected_genes) >= 1:
            data = data[data["GENE"].isin(selected_genes)]
        return data

    @app.callback(
        Output("mutation_heatmap", "figure"),
        Input("mutation_heatmap-select_sample", "value"),
        Input("mutation_heatmap-gene_dropdown", "value"),
    )
    def update_graph(sample_ids: str, genes: list):
        fig = get_figure(df, sample_ids, genes)
        return fig

    return app
