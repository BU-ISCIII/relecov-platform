"""
Mutation heatmap

- Read mutation data
- Process data
- Create plotly heatmap:
    - Rows are samples
    - Mutations are columns
    - Color represents allele frequency

"""
# import os
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px

import pandas as pd
from relecov_core.utils.handling_variant import (
    # get_if_chromosomes_exists,
    # get_if_organism_exists,
    get_position_per_sample,
    get_alelle_frequency_per_sample,
    # create_effect_list,
)
from relecov_core.utils.handling_samples import get_sample_obj_from_sample_name
from relecov_core.models import Effect, Gene, VariantAnnotation, VariantInSample

"""
from relecov_dashboard.utils.graphics.mutation_table_copy import (
    read_mutation_data,
    process_mutation_df,
)
"""
# from relecov_platform import settings




def create_data_for_dataframe(sample_name):
    # "B.1.1.7", "NC_045512"
    df = {}
    list_of_hgvs_p = []
    gene_list = []
    effect_list = []
    sample_list = []
    lineage_list = ["B.1.1.7", "B.1.1.7", "B.1.1.7", "B.1.1.7", "B.1.1.7"]
    chromosome = "NC_045512"
    sample_obj = get_sample_obj_from_sample_name(sample_name=sample_name)
    if sample_obj is not None:
        af = get_alelle_frequency_per_sample(
            sample_name=sample_name, chromosome=chromosome
        )
        pos = get_position_per_sample(sample_name=sample_name, chromosome=chromosome)
        variant_in_sample_objs = VariantInSample.objects.filter(sampleID_id=sample_obj)
        for variant_in_sample_obj in variant_in_sample_objs:
            variant_annotation_objs = VariantAnnotation.objects.filter(
                variantID_id=variant_in_sample_obj.get_variantID_id()
            )
            for variant_annotation_obj in variant_annotation_objs:
                hgvs_p = variant_annotation_obj.get_variant_in_sample_data()[1]
                list_of_hgvs_p.append(hgvs_p)

                geneID_id = variant_annotation_obj.get_geneID_id()
                gene_obj = Gene.objects.filter(gene_name__iexact=geneID_id).last()
                gene_list.append(gene_obj.get_gene_name())

                effect_obj = Effect.objects.filter(
                    effect__iexact=variant_annotation_obj.get_effectID_id()
                ).last()
                effect_list.append(effect_obj.get_effect())

                sample_list.append(sample_name)

        df["SAMPLE"] = sample_list
        df["POS"] = pos
        df["Mutation"] = list_of_hgvs_p
        df["AF"] = af
        df["EFFECT"] = effect_list
        df["GENE"] = gene_list
        df["LINEAGE"] = lineage_list

        return df
    else:
        return None


# (data: pd.DataFrame, sample_ids: list, genes: list = None):
def get_figure(df, sample_name):
    # df = create_data_for_dataframe(sample_name=sample_name)
    """
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
    """
    # Heatmap
    fig = px.imshow(
        # pivot_df,
        df,
        aspect="auto",
        labels=dict(x="Mutation", y="Sample", color="AF"),
        color_continuous_scale="RdYlGn",
        range_color=[0, 1],
    )
    fig.update(layout_coloraxis_showscale=True, layout_showlegend=False)
    fig.update_layout(
        yaxis={"title": "Samples"},
        xaxis={"title": "Mutations", "tickangle": 45},
        yaxis_nticks=len(df) if len(df) <= 50 else 50,
        xaxis_nticks=len(df.columns) if len(df.columns) <= 100 else 100,
    )
    fig.update_traces(xgap=1)

    return fig


def create_hot_map(sample_name):
    df = create_data_for_dataframe(sample_name=sample_name)
    get_figure(df, sample_name)
    """
    input_file = os.path.join(
        settings.BASE_DIR, "relecov_core", "docs", "variants_long_table_last.csv"
    )
    sample_ids = [2018185, 210067]
    df = read_mutation_data(input_file, file_extension="csv")
    df = process_mutation_df(df)
    print(df)

    all_genes = list(df["GENE"].unique())
    all_sample_ids = list(df["SAMPLE"].unique())
    """
    all_genes = list(df["GENE"])
    all_sample_ids = list(df["SAMPLE"])

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
                        value=all_sample_ids,
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
                figure=get_figure(df, all_sample_ids),
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
