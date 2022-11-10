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
        )

from relecov_core.models import (
        LineageValues,
        Sample
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

    lineage_value_objs = LineageValues.objects.filter(value__iexact=lineage)
    sample_objs = Sample.objects.filter(linage_values__in=lineage_value_objs)
    #variants=VariantInSample.objects.filter(sampleID_id__in=sample_objs, af__gt=0.75).values_list("variantID_id",flat=True).distinct()e
    # VariantInSample.objects.filter(sampleID_id__in=sample_objs, variantID_id=variants[0]).values_list("sampleID_id").count()
    """
    lineage_fields_obj = LineageFields.objects.filter(
        property_name="lineage_name"
    ).last()
    lineage_value_obj = LineageValues.objects.filter(
        lineage_fieldID=lineage_fields_obj.get_lineage_field_id(), value=lineage
    ).last()
    sample_objs = Sample.objects.filter(linage_values=lineage_value_obj)
    """
    for sample_obj in sample_objs:
        af = get_alelle_frequency_per_sample(
            sample_obj.get_sequencing_sample_id(), chromosome
        )
        pos = get_position_per_sample(sample_obj.get_sequencing_sample_id(), chromosome)
        effects = create_effect_list(sample_obj.get_sequencing_sample_id(), chromosome)

        list_of_af += af
        list_of_pos += pos
        list_of_effects += effects

    mdata["x"] = list_of_pos
    mdata["y"] = list_of_af
    mdata["mutationGroups"] = list_of_effects
    mdata["domains"] = domains

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
