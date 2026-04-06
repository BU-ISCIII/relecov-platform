"""
Mutation table under needle plot
- Read JSON/CSV
- Generate dataframe
- Clean or filter dataframe
- Generate auxiliar table to needle plot
"""

# Generic imports
import pandas as pd

# Local imports
import core.models
import core.utils.samples
import core.utils.variants

"""
import core.utils.handling_variant
"""


# FIXME: This file is not accessed.
def create_dataframe(sample_list, effect_list):
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
        sample_obj = core.utils.samples.get_sample_obj_from_sample_name(
            sample_name=sample_name
        )
        if sample_obj is not None:
            variant_in_sample_objs = core.models.VariantInSample.objects.filter(
                sampleID_id=sample_obj
            )

            for variant_in_sample_obj in variant_in_sample_objs:
                variant_annotation_obj = core.models.VariantAnnotation.objects.filter(
                    variantID_id=variant_in_sample_obj.get_variantID_id()
                ).last()
                effect_obj = core.models.Effect.objects.filter(
                    effect__iexact=variant_annotation_obj.get_effectID_id()
                ).last()
                if effect_obj.get_effect() in effect_list:
                    hgvs_p = variant_annotation_obj.get_variant_in_sample_data()[1]
                    list_of_hgvs_p.append(hgvs_p)

                    geneID_id = variant_annotation_obj.get_geneID_id()
                    gene_obj = core.models.Gene.objects.filter(
                        gene_name__iexact=geneID_id
                    ).last()
                    gene_list.append(gene_obj.get_gene_name())

                    effect_obj = core.models.Effect.objects.filter(
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


def get_default_sample_and_effect_options():
    chromosome_obj = core.utils.variants.get_default_chromosome()
    if chromosome_obj is None:
        return [], []
    sample_list = core.utils.variants.get_sample_in_variant_list(chromosome_obj)
    if not sample_list:
        return [], []
    df = create_dataframe(
        sample_list=sample_list,
        effect_list=list(core.models.Effect.objects.values_list("effect", flat=True)),
    )
    if df.empty:
        return sample_list, []
    return sample_list, list(df["EFFECT"].dropna().unique())


def create_mutation_table(sample_list, effect_list):
    df = create_dataframe(sample_list=sample_list, effect_list=effect_list)
    return df.to_dict("records")

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
