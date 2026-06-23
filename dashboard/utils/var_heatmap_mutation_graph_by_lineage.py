"""
Mutation heatmap

- Read mutation data
- Process data
- Create plotly heatmap:
    - Rows are samples
    - Mutations are columns
    - Color represents allele frequency

"""

# Generic imports
import pandas as pd
import plotly.express as px

# Local imports
import core.models
import core.utils.samples
import core.utils.variants


def create_dataframe(sample_list, gene_list):
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
                if variant_annotation_obj.get_geneID_id() in gene_list:
                    hgvs_p = variant_annotation_obj.get_variant_in_sample_data()[1]
                    list_of_hgvs_p.append(hgvs_p)

                    geneID_id = variant_annotation_obj.get_geneID_id()
                    gene_obj = core.models.Gene.objects.filter(
                        gene_name__iexact=geneID_id
                    ).last()
                    gene_list_df.append(gene_obj.get_gene_name())

                    effect_obj = core.models.Effect.objects.filter(
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


def get_default_sample_and_gene_options():
    chromosome_obj = core.utils.variants.get_default_chromosome()
    if chromosome_obj is None:
        return [], []
    gene_list = core.utils.variants.get_gene_list(chromosome_obj)
    sample_list = core.utils.variants.get_sample_in_variant_list(chromosome_obj)
    return sample_list, gene_list


def empty_heatmap_figure():
    fig = px.imshow(
        [[None]],
        labels=dict(x="Mutation", y="Sample", color="AF"),
        color_continuous_scale="RdYlGn",
        range_color=[0, 1],
    )
    fig.update_layout(
        title="No mutation data available",
        yaxis={"title": "Samples"},
        xaxis={"title": "Mutations", "tickangle": 45},
        coloraxis_showscale=True,
        showlegend=False,
    )
    return fig


def get_figure(data: pd.DataFrame, sample_ids: list, genes: list):
    if data.empty:
        return empty_heatmap_figure()
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
    fig.update_layout(coloraxis_showscale=True, showlegend=False)
    fig.update_layout(
        yaxis={"title": "Samples"},
        xaxis={"title": "Mutations", "tickangle": 45},
        yaxis_nticks=len(pivot_df) if len(pivot_df) <= 50 else 50,
        xaxis_nticks=len(pivot_df.columns) if len(pivot_df.columns) <= 100 else 100,
    )
    fig.update_traces(xgap=1)

    return fig


def get_heatmap_options():
    sample_list, gene_list = get_default_sample_and_gene_options()
    df = create_dataframe(sample_list=sample_list, gene_list=gene_list)
    all_genes = list(df["GENE"].unique()) if not df.empty else gene_list
    all_sample_ids = list(df["SAMPLE"].unique()) if not df.empty else sample_list
    return all_sample_ids, all_genes


def create_heatmap(sample_list, gene_list):
    df = create_dataframe(sample_list=sample_list, gene_list=gene_list)
    return get_figure(df, sample_list, genes=gene_list)
