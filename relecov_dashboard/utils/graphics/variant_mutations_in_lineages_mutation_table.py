"""
Mutation table under needle plot
- Read JSON/CSV
- Generate dataframe
- Clean or filter dataframe
- Generate auxiliar table to needle plot
"""
import pandas as pd

from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash
import dash_table
from relecov_core.models import Effect, Gene, VariantAnnotation, VariantInSample
from relecov_core.utils.handling_samples import get_sample_obj_from_sample_name

"""
from relecov_core.utils.handling_variant import (
    # get_if_chromosomes_exists,
    # get_if_organism_exists,
    get_position_per_sample,
    get_alelle_frequency_per_sample,
    # create_effect_list,
)
"""


def create_data_for_dataframe(sample_list, effect_list):
    # "B.1.1.7", "NC_045512"
    df = {}
    list_of_hgvs_p = []
    gene_list = []
    effect_list_df = []
    sample_list_df = []
    lineage_list = []
    af_list = []
    pos_list = []
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
                effect_obj = Effect.objects.filter(
                    effect__iexact=variant_annotation_obj.get_effectID_id()
                ).last()
                if effect_obj.get_effect() in effect_list:
                    hgvs_p = variant_annotation_obj.get_variant_in_sample_data()[1]
                    list_of_hgvs_p.append(hgvs_p)

                    geneID_id = variant_annotation_obj.get_geneID_id()
                    gene_obj = Gene.objects.filter(gene_name__iexact=geneID_id).last()
                    gene_list.append(gene_obj.get_gene_name())

                    effect_obj = Effect.objects.filter(
                        effect__iexact=variant_annotation_obj.get_effectID_id()
                    ).last()
                    effect_list_df.append(effect_obj.get_effect())

                    sample_list_df.append(sample_name)
                    lineage_list.append("B.1.1.7")
                    af_list.append(variant_in_sample_obj.get_af())
                    pos_list.append(variant_in_sample_obj.get_variant_pos())

        df["SAMPLE"] = sample_list_df
        df["POS"] = pos_list
        df["MUTATION"] = list_of_hgvs_p
        df["AF"] = af_list
        df["EFFECT"] = effect_list_df
        df["GENE"] = gene_list
        df["LINEAGE"] = lineage_list

    df_pandas = pd.DataFrame.from_dict(df)
    return df_pandas


def create_mutation_table(sample_list, effect_list):
    df = create_data_for_dataframe(sample_list=sample_list, effect_list=effect_list)
    all_effects = list(df["EFFECT"].unique())
    PAGE_SIZE = 20

    app = DjangoDash("mutationTable")

    app.layout = html.Div(
        children=[
            # html.P(id="mutation_table-message"),
            html.P("Select effects"),
            dcc.Dropdown(
                id="mutation_table-effect_dropdown",
                options=[{"label": i, "value": i} for i in all_effects],
                clearable=False,
                multi=True,
                value=all_effects,
                style={"width": "400px"},
                placeholder="Mutation effect",
            ),
            html.Br(),
            dash_table.DataTable(
                id="mutation_datatable",
                data=df.to_dict("records"),
                columns=[{"name": i, "id": i} for i in df.columns],
                page_current=0,
                page_size=PAGE_SIZE,
                page_action="custom",
            ),
        ]
    )

    @app.callback(
        Output("mutation_datatable", "data"),
        Input("mutation_table-effect_dropdown", "value"),
    )
    def update_selected_effects(selected_effects):
        data = {}
        sample_list = [2018185, 210067]

        if type(selected_effects) == list and len(selected_effects) >= 1:

            df = create_data_for_dataframe(
                sample_list=sample_list, effect_list=selected_effects
            )
            data = df.to_dict("records")
        return data

    """
    @app.callback(
        Output("mutation_table-message", "children"),
        Input("mutation_datatable", "active_cell"),
    )
    def show_clicks(active_cell):
        if active_cell:
            return str(active_cell)
        else:
            return "Click the table"
    """
