"""
Mutation heatmap

- Read mutation data
- Process data
- Create plotly heatmap:
    - Rows are samples
    - Mutations are columns
    - Color represents allele frequency

"""
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
from relecov_core.utils.handling_samples import get_sample_obj_from_sample_name
from relecov_core.models import Effect, Gene, VariantAnnotation, VariantInSample

"""
from relecov_core.utils.handling_variant import (
    # get_if_chromosomes_exists,
    # get_if_organism_exists,
    get_position_per_sample,
    get_alelle_frequency_per_sample,
    # create_effect_list,
)
"""


def create_data_for_dataframe(sample_list, gene_list):
    df = {}
    list_of_hgvs_p = []
    gene_list_df = []
    effect_list = []
    pos_list = []
    af_list = []
    sample_list_df = []
    lineage_list = []
    # chromosome = "NC_045512"
    for sample_name in sample_list:
        sample_obj = get_sample_obj_from_sample_name(sample_name=sample_name)

        if sample_obj is not None:
            variant_in_sample_objs = VariantInSample.objects.filter(
                sampleID_id=sample_obj
            )
            for variant_in_sample_obj in variant_in_sample_objs:
                variant_annotation_obj = VariantAnnotation.objects.filter(
                    variantID_id=variant_in_sample_obj.get_variantID_id()
                ).last()
                if variant_annotation_obj.get_geneID_id() in gene_list:
                    hgvs_p = variant_annotation_obj.get_variant_in_sample_data()[1]
                    list_of_hgvs_p.append(hgvs_p)

                    geneID_id = variant_annotation_obj.get_geneID_id()
                    gene_obj = Gene.objects.filter(gene_name__iexact=geneID_id).last()
                    gene_list_df.append(gene_obj.get_gene_name())

                    effect_obj = Effect.objects.filter(
                        effect__iexact=variant_annotation_obj.get_effectID_id()
                    ).last()
                    effect_list.append(effect_obj.get_effect())
                    sample_list_df.append(sample_name)
                    lineage_list.append("B.1.1.7")
                    af_list.append(variant_in_sample_obj.get_af())
                    pos_list.append(variant_in_sample_obj.get_variant_pos())

    df["SAMPLE"] = sample_list_df
    df["POS"] = pos_list
    df["MUTATION"] = list_of_hgvs_p
    df["AF"] = af_list
    df["EFFECT"] = effect_list
    df["GENE"] = gene_list_df
    df["LINEAGE"] = lineage_list

    pandas_df = pd.DataFrame.from_dict(df)

    return pandas_df


def get_figure(data: pd.DataFrame, sample_ids: list, genes: list):
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


def create_heat_map(sample_list, gene_list):
    df = create_data_for_dataframe(sample_list=sample_list, gene_list=gene_list)
    get_figure(df, sample_list, genes=gene_list)

    all_genes = list(df["GENE"].unique())
    all_sample_ids = list(df["SAMPLE"].unique())

    app = DjangoDash("mutationHeatmap")
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
                        id="mutation_heatmap_select_sample",
                        options=[{"label": i, "value": i} for i in all_sample_ids],
                        clearable=False,
                        multi=True,
                        value=all_sample_ids,
                        style={"width": "500px", "margin-right": "30px"},
                    ),
                    dcc.Dropdown(
                        id="mutation_heatmap_gene_dropdown",
                        options=[{"label": i, "value": i} for i in all_genes],
                        clearable=False,
                        multi=True,
                        value=all_genes,
                        style={"width": "400px", "margin-right": "30px"},
                        placeholder="Filter genes",
                    ),
                ],
            ),
            dcc.Graph(
                id="mutation_heatmap_graph",
                figure=get_figure(df, all_sample_ids, genes=None),
                # style={"width": "1500px", "height": "700px"},
            ),
        ]
    )

    @app.callback(
        Output("mutation_heatmap_graph", "figure"),
        Input("mutation_heatmap_select_sample", "value"),
        Input("mutation_heatmap_gene_dropdown", "value"),
    )
    def update_selected_sample(selected_sample: int, selected_genes):
        data = create_data_for_dataframe(
            sample_list=list(selected_sample), gene_list=selected_genes
        )
        fig = get_figure(data, selected_sample, genes=selected_genes)
        return fig
