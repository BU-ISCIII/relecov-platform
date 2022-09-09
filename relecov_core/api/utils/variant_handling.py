from relecov_core.api.serializers import (
    CreateEffectSerializer,
    CreateFilterSerializer,
    CreateVariantInSampleSerializer,
    CreateVariantAnnotationSerializer,
    CreateVariantSerializer,
)
from relecov_core.core_config import (
    ERROR_GENE_NOT_DEFINED_IN_DATABASE,
    ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE,
    ERROR_UNABLE_TO_STORE_IN_DATABASE,
)

from relecov_core.models import (
    Effect,
    Filter,
    Variant,
)

from relecov_core.utils.handling_variant import (
    get_if_chromosomes_exists,
    get_gene_obj_from_gene_name,
)


def create_or_get_filter_obj(filter_value):
    """Return the filter instance or create if not exists"""
    if Filter.objects.filter(filter__iexact=filter_value).exists():
        return Filter.objects.filter(filter__iexact=filter_value).last()
    filter_serializer = CreateFilterSerializer(data={"filter": filter_value})
    if filter_serializer.is_valid():
        filter_obj = filter_serializer.save()
        return filter_obj
    return {"ERROR": ERROR_UNABLE_TO_STORE_IN_DATABASE}


def create_or_get_effect_obj(effect_value):
    """Return the effect instance or create if not exists"""
    if Effect.objects.filter(effect__iexact=effect_value).exists():
        return Effect.objects.filter(effect__iexact=effect_value).last()
    effect_serializer = CreateEffectSerializer(data={"effect": effect_value})
    if effect_serializer.is_valid():
        effect_obj = effect_serializer.save()
        return effect_obj
    print("Here")

    return {"ERROR": ERROR_UNABLE_TO_STORE_IN_DATABASE}


def delete_created_variancs(v_in_sample_list, v_an_list):
    for item in v_in_sample_list:
        item.delete()
    for item in v_an_list:
        item.delete()
    return


def store_variant_annotation(v_ann_data):
    v_ann_serializer = CreateVariantAnnotationSerializer(data=v_ann_data)
    if not v_ann_serializer.is_valid():
        return {"ERROR": ERROR_UNABLE_TO_STORE_IN_DATABASE}
    v_ann_obj = v_ann_serializer.save()
    return v_ann_obj


def store_variant_in_sample(v_data):
    v_in_sample_serializer = CreateVariantInSampleSerializer(data=v_data)
    if not v_in_sample_serializer.is_valid():
        return {"ERROR": ERROR_UNABLE_TO_STORE_IN_DATABASE}
    v_obj = v_in_sample_serializer.save()
    return v_obj


def get_variant_id(data):
    """look out for the necessary reference ids to create the variance instance"""
    # chr = data["Chromosome"].split(".")[0]
    print(data)
    chr = "NC_045512"
    chr_obj = get_if_chromosomes_exists(chr)
    if chr_obj is None:
        return {"ERROR": ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE}
    variant_obj = Variant.objects.filter(
        chromosomeID_id=chr_obj,
        pos__iexact=data["Position"]["pos"],
        alt__iexact=data["Position"]["alt"],
    ).last()
    if variant_obj is None:
        # Create the variant
        filter_obj = create_or_get_filter_obj(data["Filter"]["filter"])
        if isinstance(filter_obj, dict):
            return filter_obj
        variant_dict = {}
        variant_dict["chromosomeID_id"] = chr_obj.get_chromosome_id()
        variant_dict["filterID_id"] = filter_obj.get_filter_id()
        variant_dict["pos"] = data["Position"]["pos"]
        variant_dict["alt"] = data["Position"]["alt"]
        variant_dict["ref"] = data["Variant"]["ref"]
        variant_serializer = CreateVariantSerializer(data=variant_dict)
        if not variant_serializer.is_valid():
            return {"ERROR": ERROR_UNABLE_TO_STORE_IN_DATABASE}
        variant_obj = variant_serializer.save()
    return variant_obj.get_variant_id()


def get_required_variant_ann_id(data):
    """Look for the ids that variant annotation needs"""
    v_ann_ids = {}
    gene_obj = get_gene_obj_from_gene_name(data["Gene"]["gene"])

    if gene_obj is None:
        return {"ERROR": ERROR_GENE_NOT_DEFINED_IN_DATABASE}
    v_ann_ids["geneID_id"] = gene_obj.get_gene_id()
    effect_obj = create_or_get_effect_obj(data["Effect"]["effect"])
    if isinstance(effect_obj, dict):
        return effect_obj
    v_ann_ids["geneID_id"] = gene_obj.get_gene_id()
    v_ann_ids["effectID_id"] = effect_obj.get_effect_id()
    return v_ann_ids


def split_variant_data(data, sample_obj):

    split_data = {"variant_in_sample": {}, "variant_ann": {}}
    split_data["variant_in_sample"]["sampleID_id"] = sample_obj.get_sample_id()
    variant_id = get_variant_id(data)
    if isinstance(variant_id, dict):
        return variant_id
    split_data["variant_in_sample"]["variantID_id"] = variant_id
    split_data["variant_in_sample"].update(data["VariantInSample"])

    v_ann_id = get_required_variant_ann_id(data)
    if "ERROR" in v_ann_id:
        return v_ann_id
    split_data["variant_ann"] = v_ann_id
    split_data["variant_ann"]["variantID_id"] = variant_id
    split_data["variant_ann"]["hgvs_c"] = data["Effect"]["hgvs_c"]
    split_data["variant_ann"]["hgvs_p"] = data["Effect"]["hgvs_p"]
    split_data["variant_ann"]["hgvs_p_1_letter"] = data["Effect"]["hgvs_p_1_letter"]

    # split_data["variant_ann"].update(data["VariantAnnotation"])
    return split_data
