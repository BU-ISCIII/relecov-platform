from relecov_dashboard.models import (
    GraphicName,
    GraphicField,
    GraphicValue,
    GraphicJsonFile,
)
from relecov_core.utils.handling_variant import (
    get_domains_and_coordenates,
    get_default_chromosome,
)

from relecov_core.utils.handling_lineage import (
    get_lineages_list,
)

from relecov_core.models import (
    LineageValues,
    Sample,
    VariantInSample,
    VariantAnnotation,
)

from relecov_core.utils.rest_api_handling import (
    fetch_samples_on_condition,
    get_stats_data,
)


def pre_proc_lineages_variations():
    """Collect the lineages information to store them at the pre-processed
    grpahic tables. Smoothing is performed before saving into database
    """
    field_names = {
        "field_1": "Collection date",
        "field_2": "Lineage",
        "field_3": "samples",
    }
    in_date_samples = fetch_samples_on_condition("collectionSampleDate")
    if "ERROR" in in_date_samples:
        return in_date_samples
    graphic_name_obj = GraphicName.objects.create_new_graphic_name(
        "lineages_variations"
    )
    field_names["graphic_name_obj"] = graphic_name_obj
    GraphicField.objects.create_new_graphic_field(field_names)

    for date, samples in in_date_samples["DATA"].items():
        lineage_in_samples = (
            LineageValues.objects.filter(
                lineage_fieldID__property_name="lineage_name",
                sample__collecting_lab_sample_id__in=samples,
            )
            .values_list("value", flat=True)
            .distinct()
        )
        for lineage in lineage_in_samples:
            value_data = {"value_1": date, "value_2": str(lineage)}
            value_data["value_3"] = Sample.objects.filter(
                collecting_lab_sample_id__in=samples,
                lineage_values__value__iexact=lineage,
            ).count()
            value_data["graphic_name_obj"] = graphic_name_obj
            GraphicValue.objects.create_new_graphic_value(value_data)
    return {"SUCCESS": "Success"}


def pre_proc_variations_per_lineage(chromosome=None):
    """Process variants per lineages"""

    lineage_data = {}

    # Grab lineages matching selected lineage
    for lineage in get_lineages_list():
        mutation_data = {}
        list_of_af = []
        list_of_pos = []
        list_of_effects = []

        lineage_value_objs = LineageValues.objects.filter(value__iexact=lineage)
        # Query samples matching that lineage
        sample_objs = Sample.objects.filter(lineage_values__in=lineage_value_objs)
        number_samples_wlineage = Sample.objects.filter(
            lineage_values__in=lineage_value_objs
        ).count()
        # Query variants with AF>0.75 for samples matching desired lineage. TODO: get this from threshold af in metadata bioinfo in db.
        variants = (
            VariantInSample.objects.filter(sampleID_id__in=sample_objs, af__gt=0.75)
            .values_list("variantID_id", flat=True)
            .distinct()
        )

        for variant in variants:
            number_samples_wmutation = (
                VariantInSample.objects.filter(
                    sampleID_id__in=sample_objs, variantID_id=variant
                )
                .values_list("sampleID_id", flat=True)
                .count()
            )
            mut_freq_population = number_samples_wmutation / number_samples_wlineage
            pos = VariantInSample.objects.filter(variantID_id=variant)[0].get_pos()

            effects = (
                VariantAnnotation.objects.filter(variantID_id__pk=variant)
                .values_list("effectID_id__effect", flat=True)
                .last()
            )

            # Only display mutations with at lease 0.05 freq in population
            if mut_freq_population > 0.05:
                list_of_af.append(mut_freq_population)
                list_of_pos.append(pos)
                list_of_effects.append(effects)

        domains = get_domains_and_coordenates(chromosome)

        mutation_data["x"] = list_of_pos
        mutation_data["y"] = list_of_af
        mutation_data["mutationGroups"] = list_of_effects
        mutation_data["domains"] = domains

        lineage_data[lineage] = mutation_data

    GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "variations_per_lineage", "graphic_data": lineage_data}
    )

    return {"SUCCESS": "Success"}


# preprocessing data for Sample processing dashboard
def pre_proc_specimen_source_pcr_1():
    """Collect the cts values when using pcr 1 and per specimen source"""
    lims_data = get_stats_data(
        {
            "sample_project_name": "Relecov",
            "project_field": "specimen_source,diagnostic_pcr_Ct_value_1",
        }
    )
    if "ERROR" in lims_data:
        return lims_data

    GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "specimen_source_pcr_1", "graphic_data": lims_data}
    )

    return {"SUCCESS": "Success"}


def pre_proc_extraction_protocol_pcr_1():
    """Collect the cts values when using pcr 1 and per specimen source"""
    lims_data = get_stats_data(
        {
            "sample_project_name": "Relecov",
            "project_field": "nucleic_acid_extraction_protocol,diagnostic_pcr_Ct_value_1",
        }
    )
    if "ERROR" in lims_data:
        return lims_data

    GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "extraction_protocol_pcr_1", "graphic_data": lims_data}
    )

    return {"SUCCESS": "Success"}


# preprocessing data for Sequencing dashboard
def pre_proc_library_kit_pcr_1():
    """Collect the cts values when using pcr 1 and per library preparation kit"""
    lims_data = get_stats_data(
        {
            "sample_project_name": "Relecov",
            "project_field": "library_preparation_kit,diagnostic_pcr_Ct_value_1",
        }
    )
    if "ERROR" in lims_data:
        return lims_data

    GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "library_kit_pcr_1", "graphic_data": lims_data}
    )

    return {"SUCCESS": "Success"}
