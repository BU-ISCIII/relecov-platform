# Generic imports
import os
import json
import logging
from datetime import datetime
from collections import OrderedDict, Counter, defaultdict
from statistics import mean
from django.db.models import (
    F,
    Count,
    Case,
    When,
    Value,
    DateField,
    CharField,
    IntegerField,
    Prefetch,
)
from django.db.models.functions import ExtractWeek, ExtractIsoYear, Concat, Cast, LPad
from django.core.paginator import Paginator

# Local imports
import core.models
import core.utils.variants
import core.utils.rest_api
import core.utils.generic_functions
import core.utils.public_db
import core.utils.bioinfo_analysis
import core.utils.lab_catalog
import dashboard.models
import dashboard.dashboard_config
import core.config

from relecov_platform import settings as relecov_platform_settings

import time

logger = logging.getLogger(__name__)


def normalize_empty_keys(data_dict, empty_label="Not Provided"):
    """
    Replace empty keys or None with `empty_label` and group the values.
    Specifically for dicts with structure: {str -> {str -> int}}
    """
    cleaned = defaultdict(dict)
    for key, inner_dict in data_dict.items():
        original_key = key
        new_key = empty_label if not key or str(key).strip() == "" else key

        if new_key != original_key:
            logger.warning(
                f"[normalize_empty_keys] Key {repr(original_key)} "
                f"converted to '{new_key}'"
            )

        for inner_k, inner_v in inner_dict.items():
            cleaned[new_key][inner_k] = cleaned[new_key].get(inner_k, 0) + inner_v

    return dict(cleaned)


def pre_proc_calculation_date():
    """Fetch the information about date for each sample to know about the
    number of days between different steps of samples
    """

    def convert_data_to_sample_dict(data, data_1, data_2):
        out_data = {}
        for item in data:
            if item[data_1] not in out_data:
                out_data[item[data_1]] = item[data_2]
        return out_data

    def convert_str_to_datetime(data, separator, invalid_samples):
        """Convert the string values to datetime object to perform calculation
        dates
        """
        # start_date is set to discard not valid dates, because they were
        # mistyped by user
        start_date = datetime.strptime("2019-12-31", "%Y-%m-%d")
        if separator:
            d_format = "%Y" + separator + "%m" + separator + "%d"
        else:
            d_format = "%Y%m%d"
        for sample in data.keys():
            if sample in invalid_samples or data[sample] is None:
                continue
            if any(x == data[sample] for x in core.config.FIELD_EMPTY_VALUES):
                continue
            if data[sample]:
                f_date = datetime.strptime(data[sample], d_format)
                if f_date < start_date:
                    invalid_samples[sample] = True
                else:
                    data[sample] = f_date
        return data, invalid_samples

    def calculate_days(sample_list, date_1, date_2):
        """Function gets 2 dictionary lists. For the same sample the subtract
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
                    continue
            else:
                continue
        return out_data

    # get sequencing date from sample table
    invalid_samples = {}
    analysis_date = core.models.BioinfoAnalysisValue.objects.filter(
        bioinfo_analysis_fieldID__property_name__exact="bioinformatics_analysis_date",
    ).values("value", "sample__sample_unique_id")
    analysis_date = convert_data_to_sample_dict(
        analysis_date, "sample__sample_unique_id", "value"
    )
    analysis_date, invalid_samples = convert_str_to_datetime(
        analysis_date, "-", invalid_samples
    )

    seq_date = core.models.Sample.objects.all().values(
        "sample_unique_id", "sequencing_date"
    )
    seq_date = convert_data_to_sample_dict(
        seq_date, "sample_unique_id", "sequencing_date"
    )

    # send request to iSkyLIMS
    collection_date = core.utils.rest_api.get_sample_parameter_data(
        "collection_sample_date"
    )
    collection_date = convert_data_to_sample_dict(
        collection_date, "Sample Name", "collection_sample_date"
    )
    collection_date, invalid_samples = convert_str_to_datetime(
        collection_date, "-", invalid_samples
    )

    recorded_date = core.utils.rest_api.get_sample_parameter_data("sample_entry_date")
    recorded_date = convert_data_to_sample_dict(
        recorded_date, "Sample Name", "sample_entry_date"
    )
    recorded_date, invalid_samples = convert_str_to_datetime(
        recorded_date, "-", invalid_samples
    )

    # perform calculation dates
    calculation_dates = {}
    sample_list = []
    for sam in seq_date.keys():
        if sam not in invalid_samples:
            sample_list.append(sam)

    # calculation_dates["samples"] = sample_list
    calculation_dates["Collection to sequencing"] = calculate_days(
        sample_list, collection_date, seq_date
    )
    calculation_dates["Sequencing to analysis"] = calculate_days(
        sample_list, seq_date, analysis_date
    )
    calculation_dates["Sequencing to DB recording"] = calculate_days(
        sample_list, seq_date, recorded_date
    )
    # json_data = json.dumps(calculation_dates)
    # Save json in database
    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "calculation_date", "graphic_data": calculation_dates}
    )

    return {"SUCCESS": "Success"}


def pre_proc_variant_graphic():
    """Collect the variant information to store them at the pre-processed
    GraphicJsonFile. Smoothing is performed before saving into database
    """
    print("Fetching collection date data from iskylims...")
    in_date_samples = core.utils.rest_api.fetch_samples_on_condition(
        "collection_sample_date"
    )
    if "ERROR" in in_date_samples:
        return in_date_samples

    date_sample = {}
    date_variant = {}
    for s_data in in_date_samples["data"]:
        if s_data["collection_sample_date"] not in date_sample:
            date_sample[s_data["collection_sample_date"]] = []
        date_sample[s_data["collection_sample_date"]].append(s_data["Sample Name"])

    print("Iterating over sample-date fetched data")
    for date, samples in date_sample.items():
        invalid_values = [
            "Omicron (Unassigned)",
            "Probable Omicron (Unassigned)",
        ]
        invalid_values.extend(core.config.FIELD_EMPTY_VALUES)
        variant_samples = (
            core.models.LineageValues.objects.filter(
                lineage_fieldID__property_name="variant_name",
                sample__sample_unique_id__in=samples,
            )
            .exclude(value__in=invalid_values)
            .values_list("value", flat=True)
            .distinct()
        )
        # Skip if no variants found
        variant_samples = [v for v in variant_samples if v]
        if not variant_samples:
            continue
        # Query sample counts instead of summing up
        sample_counts = (
            core.models.Sample.objects.filter(
                sample_unique_id__in=samples,
                lineage_values__value__in=variant_samples,
            )
            .values("lineage_values__value")  # Group by variant_name
            .annotate(count=Count("id"))  # Count samples per variant
        )

        date_samples = sum(entry["count"] for entry in sample_counts)

        # Discard variants with <5% of total samples for the date
        min_num_samples = date_samples / 20
        date_variant[date] = {
            entry["lineage_values__value"]: entry["count"]
            for entry in sample_counts
            if entry["count"] >= min_num_samples
        }

        # Remove date if no variants remain
        if not date_variant[date]:
            del date_variant[date]

    # convert dictionary to list date, variant and samples to store in json
    # for reading later as table to create the dataframe
    print("Constructing df-columns dict from date_variant data")
    collect_data = []
    num_samples_data = []
    variant_names = []
    for date_key, values in date_variant.items():
        # In order to extract ISOWeek, date must be of type datetime and not None
        if date_key is None:
            continue
        for variant_key, value in values.items():
            collect_data.append(date_key)
            variant_names.append(variant_key)
            num_samples_data.append(value)
    variant_var_data = {
        "Collection date": collect_data,
        "Lineage": variant_names,
        "samples": num_samples_data,
    }
    json_data = {
        "graphic_name": "variant_graphic_data",
        "graphic_data": variant_var_data,
    }
    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(json_data)

    return {"SUCCESS": "Success"}


def pre_proc_variations_per_lineage(chromosome=None):
    """Process variants per lineages"""

    lineage_data = {}
    invalid_lineages = [
        "Omicron (Unassigned)",
        "Probable Omicron (Unassigned)",
        "Unassigned",
    ]
    invalid_lineages.extend(core.config.FIELD_EMPTY_VALUES)
    start = time.time()
    # Grab lineages matching selected lineage
    filtered_lineage_queryset = core.models.LineageValues.objects.filter(
        lineage_fieldID__property_name="lineage_assignment",
    ).exclude(value__in=invalid_lineages)
    valid_lineages = filtered_lineage_queryset.values_list(
        "value", flat=True
    ).distinct()

    print("Pre-fetching all samples and lineages...")
    all_samples = core.models.Sample.objects.prefetch_related(
        Prefetch("lineage_values", queryset=filtered_lineage_queryset)
    )
    lineage_samples_map = defaultdict(list)
    for sample in all_samples:
        for lineage in sample.lineage_values.all():
            lineage_samples_map[lineage.value].append(sample)
    for lineage in valid_lineages:
        print(f"Processing lineage {lineage}")
        mutation_data = {}
        list_of_af = []
        list_of_pos = []
        list_of_effects = []

        sample_objs = lineage_samples_map.get(lineage, [])
        number_samples_wlineage = len(sample_objs)
        # Query variants with AF>0.75 for samples matching desired lineage. TODO: get this from threshold AF in metadata bioinfo in db.
        variants = (
            core.models.VariantInSample.objects.filter(
                sampleID_id__in=sample_objs, af__gt=0.75
            )
            .values_list("variantID_id", flat=True)
            .distinct()
        )
        variant_sample_counts_pos = (
            core.models.VariantInSample.objects.filter(
                sampleID_id__in=sample_objs, variantID_id__in=variants
            )
            .values("variantID_id")
            .annotate(sample_count=Count("sampleID_id"))
            .annotate(pos=F("variantID_id__pos"))
        )
        poscount_variant_dict = {
            entry["variantID_id"]: {
                "sample_count": entry["sample_count"],
                "pos": entry["pos"],
            }
            for entry in variant_sample_counts_pos
        }
        for variant in variants:
            if variant not in poscount_variant_dict.keys():
                print(f"Could not find variant {variant} in database")
                continue
            number_samples_wmutation = poscount_variant_dict[variant]["sample_count"]
            mut_freq_population = number_samples_wmutation / number_samples_wlineage
            pos = poscount_variant_dict[variant]["pos"]

            effects = (
                core.models.VariantAnnotation.objects.filter(variantID_id__pk=variant)
                .values_list("effectID_id__effect", flat=True)
                .last()
            )

            # Only display mutations with at lease 0.05 freq in population
            if mut_freq_population > 0.05:
                list_of_af.append(mut_freq_population)
                list_of_pos.append(pos)
                list_of_effects.append(effects)

        domains = core.utils.variants.get_domains_and_coordenates(chromosome)

        mutation_data["x"] = list_of_pos
        mutation_data["y"] = list_of_af
        mutation_data["mutationGroups"] = list_of_effects
        mutation_data["domains"] = domains
        mutation_data["SamplesWithLineage"] = number_samples_wlineage

        lineage_data[lineage] = mutation_data
    print(f"Took {start - time.time()} seconds to process all lineages")
    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "variations_per_lineage", "graphic_data": lineage_data}
    )

    return {"SUCCESS": "Success"}


# preprocessing data for Sample processing dashboard
def pre_proc_specimen_source_pcr_1():
    """Collect the cts values when using pcr 1 and per specimen source"""
    lims_data = core.utils.rest_api.get_stats_data(
        {
            "sample_project_name": "Relecov",
            "project_field": "specimen_source,diagnostic_pcr_Ct_value_1",
        }
    )
    if "ERROR" in lims_data:
        return lims_data

    cleaned_data = normalize_empty_keys(lims_data)

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "specimen_source_pcr_1", "graphic_data": cleaned_data}
    )

    return {"SUCCESS": "Success"}


def pre_proc_extraction_protocol_pcr_1():
    """Collect the cts values when using pcr 1 and per specimen source"""
    lims_data = core.utils.rest_api.get_stats_data(
        {
            "sample_project_name": "Relecov",
            "project_field": "nucleic_acid_extraction_protocol,diagnostic_pcr_Ct_value_1",
        }
    )
    if "ERROR" in lims_data:
        return lims_data
    cleaned_data = normalize_empty_keys(lims_data)

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "extraction_protocol_pcr_1", "graphic_data": cleaned_data}
    )

    return {"SUCCESS": "Success"}


def _pre_proc_simple_lims_counts(graphic_name, project_field, empty_label=None):
    """Fetch and cache simple value->count stats from iSkyLIMS."""
    lims_data = core.utils.rest_api.get_stats_data(
        {
            "sample_project_name": "Relecov",
            "project_field": project_field,
        }
    )
    if "ERROR" in lims_data:
        return lims_data

    cleaned_data = {}
    for key, value in lims_data.items():
        new_key = key
        if empty_label is not None and (not key or str(key).strip() == ""):
            new_key = empty_label
        cleaned_data[new_key] = cleaned_data.get(new_key, 0) + value

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": graphic_name, "graphic_data": cleaned_data}
    )

    return {"SUCCESS": "Success"}


def pre_proc_nucleic_acid_extraction_protocol():
    """Collect counts for nucleic acid extraction protocol for methodology."""
    return _pre_proc_simple_lims_counts(
        "nucleic_acid_extraction_protocol",
        "nucleic_acid_extraction_protocol",
        empty_label="Not Provided",
    )


def pre_proc_sequencing_instrument_platform():
    """Collect counts for sequencing instrument platform for methodology."""
    return _pre_proc_simple_lims_counts(
        "sequencing_instrument_platform",
        "sequencing_instrument_platform",
        empty_label="Not Provided",
    )


def pre_proc_sequencing_instrument_model():
    """Collect counts for sequencing instrument model for methodology."""
    return _pre_proc_simple_lims_counts(
        "sequencing_instrument_model",
        "sequencing_instrument_model",
        empty_label="Not Provided",
    )


def pre_proc_library_preparation_kit():
    """Collect counts for library preparation kit for methodology."""
    return _pre_proc_simple_lims_counts(
        "library_preparation_kit",
        "library_preparation_kit",
        empty_label="Not Applicable",
    )


def pre_proc_read_length():
    """Collect counts for read length for methodology."""
    return _pre_proc_simple_lims_counts(
        "read_length",
        "read_length",
    )


# preprocessing data for Sequencing dashboard
def pre_proc_library_kit_pcr_1():
    """Collect the cts values when using pcr 1 and per library preparation kit"""
    lims_data = core.utils.rest_api.get_stats_data(
        {
            "sample_project_name": "Relecov",
            "project_field": "library_preparation_kit,diagnostic_pcr_Ct_value_1",
        }
    )
    if "ERROR" in lims_data:
        return lims_data

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "library_kit_pcr_1", "graphic_data": lims_data}
    )

    return {"SUCCESS": "Success"}


def pre_proc_based_pairs_sequenced():
    based_pairs = {}
    pcr_ct_1_values = core.utils.rest_api.get_sample_parameter_data(
        {"sample_project_name": "Relecov", "parameter": "diagnostic_pcr_Ct_value_1"}
    )
    samps_db = set(
        x[0] for x in core.models.Sample.objects.all().values_list("sample_unique_id")
    )
    if "ERROR" in pcr_ct_1_values:
        return pcr_ct_1_values
    for ct_value in pcr_ct_1_values:
        sample_name = ct_value["Sample name"]

        if sample_name not in samps_db:
            continue

        base_value_qs = core.models.BioinfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID__property_name__exact="number_of_reads_sequenced",
            sample__sample_unique_id__exact=sample_name,
        ).last()

        if base_value_qs is None:
            continue

        base_value = base_value_qs.get_value()
        try:
            float_base_value = float(ct_value["diagnostic_pcr_Ct_value_1"])
            base_value_int = int(base_value)
        except ValueError:
            continue
        if base_value_int not in based_pairs:
            based_pairs[base_value_int] = []
        based_pairs[base_value_int].append(float_base_value)

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "ct_number_of_base_pairs_sequenced",
            "graphic_data": based_pairs,
        }
    )
    return {"SUCCESS": "Success"}


# data preparation for methodology bioinfo dashboard
def pre_proc_depth_variants():
    depth_sample_list = core.models.BioinfoAnalysisValue.objects.filter(
        bioinfo_analysis_fieldID__property_name__exact="depth_of_coverage_value"
    ).values("value", "sample__sample_fingerprint")
    variant_sample_list = core.models.BioinfoAnalysisValue.objects.filter(
        bioinfo_analysis_fieldID__property_name__exact="number_of_variants_in_consensus"
    ).values("value", "sample__sample_fingerprint")
    tmp_depth = {}
    depth_variant = {}
    for item in depth_sample_list:
        try:
            tmp_depth[item["sample__sample_fingerprint"]] = float(item["value"])
        except ValueError:
            # ignore the entry if value cannot converted to float (ex. "Not Provided")
            continue
    for item in variant_sample_list:
        sample_id = item["sample__sample_fingerprint"]
        if sample_id not in tmp_depth:
            continue
        d_value = float(tmp_depth[sample_id])
        if d_value not in depth_variant:
            depth_variant[d_value] = []
        value_str = item["value"]
        if value_str is None:
            continue
        value_str = str(value_str).strip()
        if value_str.isdigit():
            depth_variant[d_value].append(int(value_str))
        else:
            continue

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "depth_variant_consensus",
            "graphic_data": depth_variant,
        }
    )
    return {"SUCCESS": "Success"}


def pre_proc_depth_sample_run():
    depth_sample_list = core.models.BioinfoAnalysisValue.objects.filter(
        bioinfo_analysis_fieldID__property_name__exact="depth_of_coverage_value"
    ).values("value", "sample__sample_unique_id")
    if len(depth_sample_list) == 0:
        return {"ERROR": "No data"}
    sample_in_run = core.utils.rest_api.get_sample_parameter_data(
        {"sample_project_name": "relecov", "parameter": "number_of_samples_in_run"}
    )
    # return error, no connection to LIMS
    if "ERROR" in sample_in_run:
        return sample_in_run
    tmp_depth = {}
    depth_sample_run = {}
    for item in depth_sample_list:
        try:
            tmp_depth[item["sample__sample_unique_id"]] = float(item["value"])
        except ValueError:
            # ignore the entry if value cannot converted to float
            continue
    for item in sample_in_run:
        try:
            int(item["number_of_samples_in_run"])
        except ValueError:
            # ignore the entry if number_of_samples cannot converted to int
            continue
        if item["Sample name"] not in tmp_depth:
            continue
        d_value = tmp_depth[item["Sample name"]]
        if d_value not in depth_sample_run:
            depth_sample_run[d_value] = []
        depth_sample_run[d_value].append(int(item["number_of_samples_in_run"]))

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "depth_samples_in_run",
            "graphic_data": depth_sample_run,
        }
    )
    return {"SUCCESS": "Success"}


def pre_proc_bioinfo_percentage_data():
    """Cache percentage distributions used in methodology bioinfo ridge plot."""
    graph_list = ["per_Ns", "per_reads_host", "per_reads_virus", "per_unmapped"]
    labels_map = {
        field.property_name: field.label_name
        for field in core.models.BioinfoAnalysisField.objects.filter(
            property_name__in=graph_list
        )
    }

    percentage_data = OrderedDict()
    rows = core.models.BioinfoAnalysisValue.objects.filter(
        bioinfo_analysis_fieldID__property_name__in=graph_list
    ).values_list(
        "bioinfo_analysis_fieldID__property_name",
        "value",
    )

    for graph in graph_list:
        percentage_data[labels_map.get(graph, graph)] = []

    for graph, value in rows:
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            try:
                numeric_value = float(str(value).replace(",", "."))
            except Exception:
                logger.warning(
                    f"Invalid value encountered in '{graph}': '{value}' could not be converted to float"
                )
                continue
        if numeric_value < 0:
            numeric_value = 0.0
        if numeric_value <= 100:
            percentage_data[labels_map.get(graph, graph)].append(numeric_value)

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "bioinfo_percentage_data",
            "graphic_data": percentage_data,
        }
    )
    return {"SUCCESS": "Success"}


def pre_proc_samples_received_map():
    geojson_file = os.path.join(
        relecov_platform_settings.STATIC_ROOT,
        "dashboard",
        "custom",
        "map",
        "spain-communities.geojson",
    )
    raw_data = core.utils.rest_api.get_summarize_data("")
    if "ERROR" in raw_data:
        return raw_data

    with open(geojson_file, encoding="utf-8") as geo_json:
        counties = json.load(geo_json)

    data = {"ccaa_id": [], "ccaa_name": [], "samples": []}
    for region in counties["features"]:
        ccaa_name = region["properties"]["name"]
        data["ccaa_id"].append(region["properties"]["cartodb_id"])
        data["ccaa_name"].append(ccaa_name)
        if ccaa_name in raw_data["region"]:
            data["samples"].append(raw_data["region"][ccaa_name])
        else:
            data["samples"].append("0")
    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {"graphic_name": "received_samples_map", "graphic_data": data}
    )
    return {"SUCCESS": "Success"}


def pre_proc_host_info():
    def split_age_in_ranges(data):
        tmp_range = {}
        invalid_data = 0
        for key, val in data.items():
            try:
                int_key = int(key)
            except ValueError:
                continue
            quotient = int_key // 10
            if quotient < 0:
                invalid_data += val
                continue
            if quotient not in tmp_range:
                tmp_range[quotient] = 0
            tmp_range[quotient] += val
        return tmp_range, invalid_data

    def fetching_data_for_range_age():
        # get stats utilization fields from LIMS
        age_years = core.utils.rest_api.get_stats_data(
            {"sample_project_name": "Relecov", "project_field": "host_age_years"}
        )
        age_months = core.utils.rest_api.get_stats_data(
            {"sample_project_name": "Relecov", "project_field": "host_age_months"}
        )
        host_age = {}
        for key, val in age_years.items():
            try:
                host_age[int(key)] = val
            except ValueError:
                continue
        for key, val in age_months.items():
            try:
                years = float(key) / 12
                if not years:
                    continue
                if years in host_age:
                    host_age[years] += val
                else:
                    host_age[years] = val
            except Exception:
                continue
        # group data by decimal range
        tmp_range, invalid_data = split_age_in_ranges(host_age)
        max_value = max(tmp_range.keys())
        host_age_range = OrderedDict()
        for idx in range(max_value + 1):
            try:
                host_age_range[dashboard.dashboard_config.HOST_RANGE_AGE_TEXT[idx]] = (
                    tmp_range[idx]
                )
            except KeyError:
                host_age_range[dashboard.dashboard_config.HOST_RANGE_AGE_TEXT[idx]] = 0
        return host_age_range, invalid_data

    def fetching_data_for_sex_and_range_data():
        years_fields = core.utils.rest_api.get_stats_data(
            {
                "sample_project_name": "Relecov",
                "project_field": "host_gender,host_age_years",
            }
        )
        months_fields = core.utils.rest_api.get_stats_data(
            {
                "sample_project_name": "Relecov",
                "project_field": "host_gender,host_age_months",
            }
        )
        max_value = 0
        invalid_data = 0
        tmp_range_per_key = {}
        host_age_range_per_key_dict = {}
        for gender, age_counts in months_fields.items():
            for age, counts in age_counts.items():
                try:
                    int(age)
                except ValueError:
                    continue
                year_age = str(int(age) / 12)
                if year_age.endswith(".0"):
                    year_age = year_age.replace(".0", "")
                if year_age in years_fields[gender]:
                    years_fields[gender][year_age] += counts
                else:
                    years_fields[gender][year_age] = counts
        for invalid_key in core.config.FIELD_EMPTY_VALUES:
            if invalid_key in years_fields:
                years_fields["Not Provided"] = {
                    k: years_fields.get("Not Provided", {}).get(k, 0)
                    + years_fields[invalid_key].get(k, 0)
                    for k in set(years_fields[invalid_key])
                    | set(years_fields.get("Not Provided", {}))
                }
                if invalid_key != "Not Provided":
                    del years_fields[invalid_key]
        for key, values in years_fields.items():
            tmp_range_per_key[key], tmp_invalid_data = split_age_in_ranges(values)
            invalid_data += tmp_invalid_data
            if tmp_range_per_key[key]:
                tmp_max_value = max(tmp_range_per_key[key].keys())
                if tmp_max_value > max_value:
                    max_value = tmp_max_value

        age_range_list = []
        for idx in range(max_value + 1):
            age_range_list.append(dashboard.dashboard_config.HOST_RANGE_AGE_TEXT[idx])
        host_age_range_per_key_dict["range_age"] = age_range_list

        for key in tmp_range_per_key.keys():
            age_range_list = []
            for idx in range(max_value + 1):
                try:
                    age_range_list.append(tmp_range_per_key[key][idx])
                except KeyError:
                    age_range_list.append(0)
            host_age_range_per_key_dict[key] = age_range_list
        return host_age_range_per_key_dict, invalid_data

    def fetching_data_for_gender():
        # get stats for host gender from LIMS
        lims_fields = core.utils.rest_api.get_stats_data(
            {"sample_project_name": "Relecov", "project_field": "host_gender"}
        )
        if "ERROR" in lims_fields:
            return lims_fields, ""
        labels = []
        values = []
        for key, val in lims_fields.items():
            labels.append(key)
            values.append(val)
        return labels, values

    total_invalid_data = {}
    host_info_json = {}
    # pie graphic for gender
    gender_label, gender_values = fetching_data_for_gender()
    if "ERROR" in gender_label:
        host_info_json["gender_label"] = {"ERROR": gender_label}
        host_info_json["gender_values"] = {"ERROR": gender_values}
    else:
        label_val_dict = dict(zip(gender_label, gender_values))
        for field in core.config.FIELD_EMPTY_VALUES:
            # Group all Not provided values together
            if field not in label_val_dict.keys() or field == "Not Provided":
                continue
            label_val_dict["Not Provided"] = (
                label_val_dict.get("Not Provided", 0) + label_val_dict[field]
            )
            del label_val_dict[field]
        host_info_json["gender_label"] = list(label_val_dict.keys())
        host_info_json["gender_values"] = list(label_val_dict.values())
    # graphic for gender and age
    host_gender_data, invalid_gender_data = fetching_data_for_sex_and_range_data()
    for field in core.config.FIELD_EMPTY_VALUES:
        # Group all Not provided values together
        if field not in host_gender_data.keys() or field == "Not Provided":
            continue
        empty_vals_zip = zip(
            host_gender_data.get("Not Provided", [0] * len(host_gender_data[field])),
            host_gender_data[field],
        )
        host_gender_data["Not Provided"] = [x + y for x, y in empty_vals_zip]
        del host_gender_data[field]
    total_invalid_data["invalid_gender_data"] = invalid_gender_data
    host_info_json["gender_data"] = host_gender_data
    host_age_data, invalid_age_data = fetching_data_for_range_age()
    total_invalid_data["invalid_age_data"] = invalid_age_data
    host_info_json["host_age_data"] = host_age_data
    host_info_json["invalid_data"] = total_invalid_data
    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "host_info",
            "graphic_data": host_info_json,
        }
    )
    return {"SUCCESS": "Success"}


def pre_proc_samples_per_date_all_lab(detailed=None):
    # Fetch a list of dictionaries of [{Sample Name: sample_name, Collection_sample_date: collection date}]
    in_date_samples = core.utils.rest_api.fetch_samples_on_condition(
        "collection_sample_date"
    )
    if "ERROR" in in_date_samples:
        return in_date_samples
    if detailed is None:
        # No group by collection institution is needed
        counted_dates = Counter(  # Use counter to get a dictionary of {date: num_samples}
            (
                datetime.strptime(x["collection_sample_date"], "%Y-%m-%d").strftime(
                    "%Y-W%V"
                )
                if isinstance(
                    x["collection_sample_date"], str
                )  # If data is in string format, convert it to date first
                else x["collection_sample_date"].strftime(
                    "%Y-W%V"
                )  # Else just process date directly
            )
            for x in in_date_samples[
                "data"
            ]  # each x is a dict of [{"Sample Name": name, "collection_sample_date": date}]
            if isinstance(
                x["collection_sample_date"], (datetime, str)
            )  # Only process data in string or date formats
        )
        # Convert the list of date strings back to datetime objects for comparison
        date_objects = [
            datetime.strptime(date + "-1", "%G-W%V-%u") for date in counted_dates.keys()
        ]
        # FIXME: This filter should not be necessary if database was correctly curated
        date_objects = [x for x in date_objects if x.year > 2019]
        # Find the earliest and latest dates
        min_date = min(date_objects)
        max_date = max(date_objects)
        # Generate all dates between min_date and max_date
        all_weeks = core.utils.generic_functions.list_all_possible_weeks(
            min_date, max_date, output_format="%Y-W%V"
        )
        # Dict keys are not ordered by default
        all_count_dates = OrderedDict()
        # Fill missing dates with 0s
        for date in all_weeks:
            all_count_dates[date] = counted_dates.get(date, 0)

        dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
            {
                "graphic_name": "samples_per_date_all_lab",
                "graphic_data": all_count_dates,
            }
        )
        return {"SUCCESS": "Success"}
    else:
        # Start processing samples per date and for each lab
        samples_dates_dict = {
            x["Sample Name"]: x["collection_sample_date"]
            for x in in_date_samples["data"]
        }
        join_conditions = [
            When(sample_unique_id=sample_id, then=Value(collect_date))
            for sample_id, collect_date in samples_dates_dict.items()
        ]
        relevant_samples = core.models.Sample.objects.filter(
            sample_unique_id__in=samples_dates_dict.keys()
        ).annotate(collecting_date=Case(*join_conditions, output_field=DateField()))

        valid_insts = relevant_samples.exclude(collecting_date__isnull=True)
        # FIXME: This filter should not be necessary if database was correctly curated
        valid_insts = valid_insts.filter(collecting_date__gte=datetime(2019, 1, 1))
        lab_date_count = (
            valid_insts.annotate(
                iso_yearweek=Concat(
                    Cast(ExtractIsoYear(F("collecting_date")), IntegerField()),
                    Value("-W"),
                    LPad(ExtractWeek(F("collecting_date")), 2, Value("0")),
                    output_field=CharField(),
                )
            )
            .values(
                "submitting_institution",
                "lab_code_1",
                "collecting_institution",
                "iso_yearweek",
            )
            .order_by("lab_code_1", "collecting_institution", "iso_yearweek")
            .annotate(num_samples=Count("iso_yearweek"))
        )

        lab_date_count_dict = {}
        for item in lab_date_count:
            raw_display = item.get("collecting_institution")
            lab_code = item.get("lab_code_1") or core.utils.lab_catalog.get_lab_code(
                raw_display
            )
            display_name = core.utils.lab_catalog.ensure_lab_display(
                lab_code, fallback_name=raw_display
            )
            key = (
                item["submitting_institution"],
                lab_code or display_name or "",
            )
            entry = lab_date_count_dict.setdefault(
                key,
                {
                    "lab_code_1": lab_code,
                    "display": display_name,
                    "legacy_collecting_institution": raw_display,
                    "dates": {},
                },
            )
            entry["dates"][item["iso_yearweek"]] = item["num_samples"]

        final_lab_dates_count = []
        for (subinst, _lab_key), info in lab_date_count_dict.items():
            dates_dict = info["dates"]
            display_name = info["display"]
            sorted_dates = sorted(
                datetime.strptime(iso + "-1", "%G-W%V-%u") for iso in dates_dict.keys()
            )
            if not sorted_dates:
                continue
            first_date = sorted_dates[0]
            last_date = sorted_dates[-1]
            date_range = core.utils.generic_functions.list_all_possible_weeks(
                first_date, last_date, output_format="%G-W%V"
            )
            for date in date_range:
                num_samples = dates_dict.get(date, 0)
                final_lab_dates_count.append(
                    {
                        "submitting_institution": subinst,
                        "collecting_institution": display_name,
                        "lab_code_1": info.get("lab_code_1"),
                        "legacy_collecting_institution": info.get(
                            "legacy_collecting_institution"
                        ),
                        "iso_yearweek": date,
                        "num_samples": num_samples,
                    }
                )
        dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
            {
                "graphic_name": "samples_per_date_all_lab_detailed",
                "graphic_data": final_lab_dates_count,
            }
        )
        return {"SUCCESS": "Success"}


def pre_proc_samples_received_per_lab():
    """Fetch the samples received per laboratory data from LIMS and save it"""
    raw_data = core.utils.rest_api.get_summarize_data("")
    if "ERROR" in raw_data:
        return raw_data

    data = {"x": [], "y": []}
    for key, value in raw_data["laboratory"].items():
        data["x"].append(key)
        data["y"].append(value)
    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "samples_received_per_lab",
            "graphic_data": data,
        }
    )
    return {"SUCCESS": "Success"}


def pre_proc_samples_received_per_ccaa():
    """Fetch the received samples per ccaa data from LIMS and save it"""
    raw_data = core.utils.rest_api.get_summarize_data("")
    if "ERROR" in raw_data:
        return raw_data

    data = {"x": [], "y": []}
    for key, value in raw_data["region"].items():
        data["x"].append(key)
        data["y"].append(value)
    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "samples_received_per_ccaa",
            "graphic_data": data,
        }
    )
    return {"SUCCESS": "Success"}


def pre_proc_intranet_gisaid_data():
    """Get the list of the accesion values for gisaid data to show in intranet"""
    gisaid_acc = core.utils.public_db.get_public_accession_from_sample_lab(
        "gisaid_accession_id", None
    )
    gisaid_data = defaultdict(list)
    for acc in gisaid_acc:
        lab_name = acc[0]
        gisaid_data[lab_name].append(acc[1:])
    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "intranet_gisaid_data",
            "graphic_data": gisaid_data,
        }
    )
    return {"SUCCESS": "Success"}


def pre_proc_intranet_ena_data():
    """Get the list of the accesion values for ena data to show in intranet"""
    ena_acc = core.utils.public_db.get_public_accession_from_sample_lab(
        "ena_sample_accession", None
    )
    ena_data = defaultdict(list)
    for acc in ena_acc:
        lab_name = acc[0]
        ena_data[lab_name].append(acc[1:])
    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "intranet_ena_data",
            "graphic_data": ena_data,
        }
    )
    return {"SUCCESS": "Success"}


def pre_proc_methodology_lims_fields_util():
    """Cache methodology index LIMS utilization summary and detail data."""
    lims_fields = core.utils.rest_api.get_stats_data({"sample_project_name": "Relecov"})
    if "ERROR" in lims_fields:
        return lims_fields

    lims_field_display_map = core.utils.rest_api.get_sample_project_field_display_map(
        "Relecov"
    )
    f_values = list(lims_fields["fields_norm"].values())
    lims_f_values = float("%.1f" % (mean(f_values) * 100)) if len(f_values) > 1 else 0

    empty_fields = len(lims_fields["always_none"]) + len(lims_fields["never_used"])
    total_fields = len(lims_fields["fields_norm"]) + empty_fields
    max_value = max(set(lims_fields["fields_value"].values()))

    field_detail_data = {
        "field_name": [],
        "field_value": [],
        "percent": [],
    }
    for key, val in lims_fields["fields_value"].items():
        field_detail_data["field_name"].append(lims_field_display_map.get(key, key))
        field_detail_data["field_value"].append(val)
        field_detail_data["percent"].append(max_value)

    util_data = {
        "lims_f_values": lims_f_values,
        "summary_lab_values": [empty_fields, total_fields],
        "field_detail_data": field_detail_data,
        "num_lab_fields": len(lims_fields["fields_value"]),
    }

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "methodology_lims_fields",
            "graphic_data": util_data,
        }
    )
    return {"SUCCESS": "Success"}


def pre_proc_bioinfo_fields_util():
    """
    It calculates the utilization of bioinfo fields (Methodology)
    and saves it in GraphicJsonFile, just like the rest of the pre-processes.
    """
    util_data = core.utils.bioinfo_analysis.get_bioinfo_analysis_fields_utilization(
        use_cache=False
    )

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "methodology_bioinfo_fields",
            "graphic_data": util_data,
        }
    )
    return {"SUCCESS": "Success"}


def pre_proc_search_samples_summary():
    """
    Get a list of tuples to fill a table in search_samples that shows
    all the available samples to the user, including important metadata
    like sample_name, collecting_institution, collection_date, lineage_name
    """
    in_date_samples = core.utils.rest_api.fetch_samples_on_condition(
        "collection_sample_date"
    )
    logger.info(f"Fetched {len(in_date_samples['data'])} samples with collection_date")
    # Prefetch only lineage_values with the desired property
    filtered_lineages = Prefetch(
        "lineage_values",
        queryset=core.models.LineageValues.objects.filter(
            lineage_fieldID__property_name="lineage_assignment"
        ).select_related("lineage_fieldID"),
        to_attr="filt_lineages",
    )
    processed_samples_qs = (
        core.models.Sample.objects.filter(
            sample_unique_id__in=[x["Sample Name"] for x in in_date_samples["data"]]
        )
        .prefetch_related(filtered_lineages)
        .order_by("id")
    )

    paginator = Paginator(
        processed_samples_qs, 500
    )  # Dont load the whole queryset at once
    match_sampdict = {}
    for page_num in paginator.page_range:
        chunk = paginator.page(page_num)
        for sample in chunk:
            sample_id = sample.sample_unique_id
            seq_id = sample.sequencing_sample_id
            display_name = sample.collecting_institution
            lab_code = sample.lab_code_1 or core.utils.lab_catalog.get_lab_code(
                display_name
            )
            sub_inst = sample.submitting_institution
            sample_pk = sample.pk
            if sample.filt_lineages:
                lineage = sample.filt_lineages[0].value
            else:
                lineage = "Not Defined"
            match_sampdict[sample_id] = (
                sample_pk,
                lineage,
                lab_code,
                display_name,
                sub_inst,
                seq_id,
            )

    final_data = defaultdict(dict)
    for s_data in in_date_samples["data"]:
        sample_name = s_data["Sample Name"]
        if sample_name not in match_sampdict.keys():
            errtxt = f"Could not find sample {sample_name} from iskylims. Skipped from search pre_proc_search_samples_summary()"
            logger.error(errtxt)
            continue
        col_date = s_data["collection_sample_date"]
        sample_pk, lineage_name, lab_code, display_name, sub_inst, seq_id = (
            match_sampdict[sample_name]
        )
        lab_identifier = lab_code or display_name or ""
        bucket = final_data[sub_inst].setdefault(
            lab_identifier,
            {
                "lab_code_1": lab_code,
                "collecting_institution": display_name,
                "rows": [],
            },
        )
        bucket["rows"].append([sample_pk, seq_id, col_date, lineage_name, display_name])
    serializable_data = {
        sub_inst: {
            lab_key: {
                "lab_code_1": info.get("lab_code_1"),
                "collecting_institution": info.get("collecting_institution"),
                "rows": info.get("rows", []),
            }
            for lab_key, info in labs.items()
        }
        for sub_inst, labs in final_data.items()
    }

    dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
        {
            "graphic_name": "search_samples_summary_table",
            "graphic_data": serializable_data,
        }
    )
    return {"SUCCESS": "Success"}
