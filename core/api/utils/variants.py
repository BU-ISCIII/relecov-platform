# Local imports
import core.models
import core.utils.variants
import core.api.serializers
import core.config


def create_or_get_filter_obj(filter_value):
    """Return the filter instance or create if not exists"""
    if core.models.Filter.objects.filter(filter__iexact=filter_value).exists():
        return core.models.Filter.objects.filter(filter__iexact=filter_value).last()
    filter_serializer = core.api.serializers.CreateFilterSerializer(
        data={"filter": filter_value}
    )
    if filter_serializer.is_valid():
        filter_obj = filter_serializer.save()
        return filter_obj
    return {"ERROR": core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}


def create_or_get_effect_obj(effect_value):
    """Return the effect instance or create if not exists"""
    if core.models.Effect.objects.filter(effect__iexact=effect_value).exists():
        return core.models.Effect.objects.filter(effect__iexact=effect_value).last()
    effect_serializer = core.api.serializers.CreateEffectSerializer(
        data={"effect": effect_value}
    )
    if effect_serializer.is_valid():
        effect_obj = effect_serializer.save()
        return effect_obj

    return {"ERROR": core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}


def delete_created_variancs(v_in_sample_list, v_an_list):
    for item in v_in_sample_list:
        item.delete()
    for item in v_an_list:
        item.delete()
    return


def store_variant_annotation(v_ann_data):
    v_ann_serializer = core.api.serializers.CreateVariantAnnotationSerializer(
        data=v_ann_data
    )
    if not v_ann_serializer.is_valid():
        return {"ERROR": core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}
    v_ann_obj = v_ann_serializer.save()
    return v_ann_obj


def store_variant_in_sample(v_data):
    v_in_sample_serializer = core.api.serializers.CreateVariantInSampleSerializer(
        data=v_data
    )
    if not v_in_sample_serializer.is_valid():
        return {"ERROR": core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}
    v_obj = v_in_sample_serializer.save()
    return v_obj


def get_variant_id(data):
    """look out for the necessary reference ids to create the variance instance"""
    chr_obj = core.utils.variants.get_if_chromosomes_exists(data["chromosome"])
    if chr_obj is None:
        return {"ERROR": core.config.ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE}
    variant_obj = core.models.Variant.objects.filter(
        chromosomeID_id=chr_obj,
        pos__iexact=data["pos"],
        alt__iexact=data["alt"],
    ).last()
    if variant_obj is None:
        # Create the variant
        filter_obj = create_or_get_filter_obj(data["Filter"])
        if isinstance(filter_obj, dict):
            return filter_obj
        variant_dict = {}
        variant_dict["chromosomeID_id"] = chr_obj.get_chromosome_id()
        variant_dict["filterID_id"] = filter_obj.get_filter_id()
        variant_dict["pos"] = data["pos"]
        variant_dict["alt"] = data["alt"]
        variant_dict["ref"] = data["ref"]
        variant_serializer = core.api.serializers.CreateVariantSerializer(
            data=variant_dict
        )
        if not variant_serializer.is_valid():
            return {"ERROR": core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}
        variant_obj = variant_serializer.save()
    return variant_obj.get_variant_id()


def get_variant_analysis_defined(s_obj):
    return core.models.VariantInSample.objects.filter(sampleID_id=s_obj).values_list(
        "analysis_date", flat=True
    )


def get_required_variant_ann_id(data):
    """Look for the ids that variant annotation needs"""
    v_ann_ids = {}
    gene_obj = core.utils.variants.get_gene_obj_from_gene_name(data["gene"])

    if gene_obj is None:
        return {"ERROR": core.config.ERROR_GENE_NOT_DEFINED_IN_DATABASE}
    v_ann_ids["geneID_id"] = gene_obj.get_gene_id()
    effect_obj = create_or_get_effect_obj(data["effect"])
    if isinstance(effect_obj, dict):
        return effect_obj
    v_ann_ids["geneID_id"] = gene_obj.get_gene_id()
    v_ann_ids["effectID_id"] = effect_obj.get_effect_id()
    return v_ann_ids


def split_variant_data(data, sample_obj, date):
    """Separate the information received into groups"""
    split_data = {"variant_in_sample": {}, "variant_ann": {}}
    split_data["variant_in_sample"]["sampleID_id"] = sample_obj.get_sample_id()

    variant_id = get_variant_id(data)
    if isinstance(variant_id, dict):
        return variant_id
    split_data["variant_in_sample"]["variantID_id"] = variant_id
    split_data["variant_in_sample"]["analysis_date"] = date

    var_keys = ["dp", "ref_dp", "alt_dp", "af"]
    data["VariantInSample"] = {x: y for x, y in data.items() if x in var_keys}
    split_data["variant_in_sample"].update(data["VariantInSample"])

    v_ann_id = get_required_variant_ann_id(data)
    if "ERROR" in v_ann_id:
        return v_ann_id
    split_data["variant_ann"] = v_ann_id
    split_data["variant_ann"]["variantID_id"] = variant_id

    annot_keys = ["hgvs_c", "hgvs_p", "hgvs_p_1_letter"]
    data["VariantAnnotation"] = {x: y for x, y in data.items() if x in annot_keys}
    split_data["variant_ann"].update(data["VariantAnnotation"])
    return split_data


def variant_annotation_exists(data):
    """Check if variant annotation exists. Return True if exists"""
    if core.models.VariantAnnotation.objects.filter(
        hgvs_c__iexact=data["hgvs_c"],
        hgvs_p__iexact=data["hgvs_p"],
        hgvs_p_1_letter__iexact=data["hgvs_p_1_letter"],
    ).exists():
        return True
    return False
