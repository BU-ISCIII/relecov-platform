from datetime import datetime
from relecov_dashboard.models import GraphicJsonFile
from relecov_core.utils.handling_variant import (
    get_domains_and_coordenates,
)

from relecov_core.utils.handling_lineage import (
    get_lineages_list,
)

from relecov_core.models import (
    LineageValues,
    Sample,
    VariantInSample,
    VariantAnnotation,
    BioinfoAnalysisValue,
)

from relecov_core.utils.rest_api_handling import (
    fetch_samples_on_condition,
    get_stats_data,
    get_sample_parameter_data,
)


def pre_proc_calculation_date():
    """Fetch the information about date for each sample to know about the
    number of days between different steps of samples
    """

    def convert_data_to_sample_dict(data, data_1, data_2):
        out_data = {}
        for item in data:
            if not item[data_1] in out_data:
                out_data[item[data_1]] = item[data_2]
        return out_data

    def convert_str_to_datetime(data, separator):
        """Convert the string values to datetime object to perform calculation
        dates
        """
        if separator:
            d_format = "%Y" + separator + "%m" + separator + "%d"
        else:
            d_format = "%Y%m%d"
        for sample in data.keys():
            if data[sample]:
                data[sample] = datetime.strptime(data[sample], d_format)
        return data

    def calculate_days(sample_list, date_1, date_2):
        """Function gets 2 dictionnary list. For the same sample the substract
        operation date_2 - date_1 is done.
        """
        out_data = []
        for sample in sample_list:
            if sample in date_1 and sample in date_2:
                try:
                    days = (date_2[sample] - date_1[sample]).days
                    if (date_2[sample] - date_1[sample]).days > 1000:
                        print(sample, "numero dias ", days)
                    out_data.append((date_2[sample] - date_1[sample]).days)
                except TypeError:
                    out_data.append("bbbb")
            else:
                out_data.append("aaaaaa")
        return out_data

    # get sequencing date from sample table
    analysis_date = BioinfoAnalysisValue.objects.filter(
        bioinfo_analysis_fieldID__property_name__exact="analysis_date",
    ).values("value", "sample__collecting_lab_sample_id")
    analysis_date = convert_data_to_sample_dict(
        analysis_date, "sample__collecting_lab_sample_id", "value"
    )
    analysis_date = convert_str_to_datetime(analysis_date, None)

    seq_date = Sample.objects.all().values(
        "collecting_lab_sample_id", "sequencing_date"
    )
    seq_date = convert_data_to_sample_dict(
        seq_date, "collecting_lab_sample_id", "sequencing_date"
    )

    # send request to iSkyLIMS
    collection_date = get_sample_parameter_data("collectionSampleDate")
    collection_date = convert_data_to_sample_dict(
        collection_date, "Sample Name", "collectionSampleDate"
    )
    collection_date = convert_str_to_datetime(collection_date, "-")

    recorded_date = get_sample_parameter_data("sampleEntryDate")
    recorded_date = convert_data_to_sample_dict(
        recorded_date, "Sample Name", "sampleEntryDate"
    )
    recorded_date = convert_str_to_datetime(recorded_date, "-")

    # perform calculation dates
    calculation_dates = {}
    sample_list = list(seq_date.keys())
    # calculation_dates["samples"] = sample_list
    calculation_dates["coll_rec_date"] = calculate_days(
        sample_list, collection_date, recorded_date
    )
    calculation_dates["seq_coll_date"] = calculate_days(
        sample_list, recorded_date, seq_date
    )
    calculation_dates["analyis_seq_date"] = calculate_days(
        sample_list, seq_date, analysis_date
    )
    # json_data = json.dumps(calculation_dates)
    # Save json in database
    GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "calculation_date", "graphic_data": calculation_dates}
    )

    return {"SUCCESS": "Success"}


def pre_proc_lineages_variations():
    """Collect the lineages information to store them at the pre-processed
    graphicJasonFile. Smoothing is performed before saving into database
    """

    in_date_samples = fetch_samples_on_condition("collectionSampleDate")
    if "ERROR" in in_date_samples:
        return in_date_samples
    collect_data = []
    num_samples_data = []
    lineage_data = []
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

            # value_data = {"value_1": date, "value_2": str(lineage)}
            collect_data.append(date)
            lineage_data.append(lineage)
            num_samples_data.append(
                Sample.objects.filter(
                    collecting_lab_sample_id__in=samples,
                    lineage_values__value__iexact=lineage,
                ).count()
            )

    lineage_var_data = {
        "Collection date": collect_data,
        "Lineage": lineage_data,
        "samples": num_samples_data,
    }
    json_data = {
        "graphic_name": "lineages_variations",
        "graphic_data": lineage_var_data,
    }
    GraphicJsonFile.objects.create_new_graphic_json(json_data)

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
