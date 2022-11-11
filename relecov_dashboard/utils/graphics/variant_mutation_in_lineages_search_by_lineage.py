from dash import dcc, html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
import dash_bio as dashbio

from relecov_core.utils.handling_variant import (
        get_default_chromosome,
        get_domains_list,
        get_alelle_frequency_per_sample,
        get_position_per_sample,
        create_effect_list,
        get_domains_and_coordenates,
        )

from relecov_core.models import (
        LineageValues,
        Sample,
        Chromosome,
        VariantInSample,
        VariantAnnotation,
        )


# ITER variant mutation
def get_variant_data_from_lineages(lineage=None, chromosome=None):
    if chromosome is None:
        chromosome = get_default_chromosome()
    mdata = {}
    list_of_af = []
    list_of_pos = []
    list_of_effects = []

    domains = get_domains_list(chromosome)
    if not LineageValues.objects.filter(
        lineage_fieldID__property_name__iexact="lineage_name"
    ).exists():
        return None
    if lineage is None:
        lineage = (
            LineageValues.objects.filter(
                lineage_fieldID__property_name__iexact="lineage_name"
            )
            .values_list("value",flat=True)
            .first()
        )

    # Grab lineages matching selected lineage
    lineage_value_objs = LineageValues.objects.filter(value__iexact=lineage)
    # Query samples matching that lineage
    sample_objs = Sample.objects.filter(lineage_values__in=lineage_value_objs)
    number_samples_wlineage = Sample.objects.filter(lineage_values__in=lineage_value_objs).count()
    # Query variants with AF>0.75 for samples matching desired lineage
    variants=VariantInSample.objects.filter(sampleID_id__in=sample_objs, af__gt=0.75).values_list("variantID_id",flat=True).distinct()

    for variant in variants:
        number_samples_wmutation = VariantInSample.objects.filter(sampleID_id__in=sample_objs, variantID_id=variant).values_list("sampleID_id").count()
        mut_freq_population = number_samples_wmutation/number_samples_wlineage
        pos = VariantInSample.objects.filter(variantID_id=variant)[0].get_pos()

        effects = list(
            VariantAnnotation.objects.filter(
                variantID_id__pk=variant
            ).values_list("effectID_id__effect", flat=True)
        )


        list_of_af.append(mut_freq_population)
        list_of_pos.append(pos)
        list_of_effects.append(effects)

    chromosome_obj = Chromosome.objects.last()
    domains = get_domains_and_coordenates(chromosome_obj)

    mdata["x"] = list_of_pos
    mdata["y"] = list_of_af
    mdata["mutationGroups"] = list_of_effects
    mdata["domains"] = domains
    import pdb; pdb.set_trace()

    return mdata

def create_needle_plot_graph_mutation_by_lineage(lineage, mdata):
    app = DjangoDash("needlePlotMutationByLineage")

    app.layout = html.Div(
        children=[
            html.Div(
                children=[
                    html.Div(
                        children=[
                            "Show or hide range slider",
                            dcc.Dropdown(
                                id="needleplot-rangeslider",
                                options=[
                                    {"label": "Show", "value": 1},
                                    {"label": "Hide", "value": 0},
                                ],
                                clearable=False,
                                multi=False,
                                value=1,
                                style={"width": "150px", "margin-right": "30px"},
                            ),
                        ]
                    ),
                    html.Div(
                        children=[
                            "Select a Lineage",
                            dcc.Dropdown(
                                id="needleplot-select-lineage",
                                options=[
                                    {"label": "B.1.1.7", "value": "B.1.1.7"}
                                ],  # dict_of_samples,
                                clearable=False,
                                multi=False,
                                value=lineage,
                                style={"width": "150px"},
                            ),
                        ]
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "start",
                    "align-items": "flex-start",
                },
            ),
            html.Div(
                children=dashbio.NeedlePlot(
                    width="auto",
                    id="dashbio-needleplot",
                    mutationData=mdata,
                    rangeSlider=True,
                    xlabel="Genome Position",
                    ylabel="Allele Frequency ",
                    domainStyle={
                        # "textangle": "45",
                        "displayMinorDomains": False,
                    },
                ),
            ),
        ]
    )

    @app.callback(
        Output("dashbio-needleplot", "mutationData"),
        Input("needleplot-select-lineage", "value"),
    )
    def update_sample(selected_lineage):
        mdata = get_variant_data_from_lineages("B.1.1.7", "NC_045512")
        create_needle_plot_graph_mutation_by_lineage(selected_lineage, mdata)
        # mutation_data = mdata
        # return mutation_data

    @app.callback(
        Output("dashbio-needleplot", "rangeSlider"),
        Input("needleplot-rangeslider", "value"),
    )
    def update_range_slider(range_slider_value):
        return True if range_slider_value else False
