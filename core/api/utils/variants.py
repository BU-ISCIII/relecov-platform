# Standard library imports
from typing import Optional

# Local imports

import core.models
import core.utils.variants
import core.api.serializers
import core.config


class VariantProcessingCache:
    """
    Lightweight cache to avoid repeated lookups and creations while processing
    the variants payload of a single request.
    """

    def __init__(self):
        self.filters = {}
        self.effects = {}
        self.chromosomes = {}
        self.genes = {}
        self.variants = {}
        self.variant_annotations = set()

    @staticmethod
    def _norm(value: Optional[str]) -> str:
        return value.casefold() if isinstance(value, str) else ""

    def cache_filter(self, value: str, obj: core.models.Filter) -> None:
        self.filters[self._norm(value)] = obj

    def get_filter(self, value: str):
        return self.filters.get(self._norm(value))

    def cache_effect(self, value: str, obj: core.models.Effect) -> None:
        self.effects[self._norm(value)] = obj

    def get_effect(self, value: str):
        return self.effects.get(self._norm(value))

    def cache_chrom(self, value: str, obj: core.models.Chromosome) -> None:
        self.chromosomes[self._norm(value)] = obj

    def get_chrom(self, value: str):
        return self.chromosomes.get(self._norm(value))

    def cache_gene(self, value: str, obj: core.models.Gene) -> None:
        self.genes[self._norm(value)] = obj

    def get_gene(self, value: str):
        return self.genes.get(self._norm(value))

    def cache_variant(self, chrom: str, pos: str, ref: str, alt: str, variant_id: int):
        key = (self._norm(chrom), pos, self._norm(ref), self._norm(alt))
        self.variants[key] = variant_id

    def get_variant(self, chrom: str, pos: str, ref: str, alt: str):
        key = (self._norm(chrom), pos, self._norm(ref), self._norm(alt))
        return self.variants.get(key)

    def has_annotation(self, hgvs_c: str, hgvs_p: str, hgvs_p1: str) -> bool:
        key = (
            self._norm(hgvs_c),
            self._norm(hgvs_p),
            self._norm(hgvs_p1),
        )
        return key in self.variant_annotations

    def cache_annotation(self, hgvs_c: str, hgvs_p: str, hgvs_p1: str) -> None:
        key = (
            self._norm(hgvs_c),
            self._norm(hgvs_p),
            self._norm(hgvs_p1),
        )
        self.variant_annotations.add(key)


def create_or_get_filter_obj(filter_value, cache=None):
    """Return the filter instance or create if not exists"""
    if cache:
        cached = cache.get_filter(filter_value)
        if cached:
            return cached
    filter_obj = core.models.Filter.objects.filter(filter__iexact=filter_value).last()
    if filter_obj:
        if cache:
            cache.cache_filter(filter_value, filter_obj)
        return filter_obj
    filter_serializer = core.api.serializers.CreateFilterSerializer(
        data={"filter": filter_value}
    )
    if filter_serializer.is_valid():
        filter_obj = filter_serializer.save()
        if cache:
            cache.cache_filter(filter_value, filter_obj)
        return filter_obj
    return {"ERROR": core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}


def create_or_get_effect_obj(effect_value, cache=None):
    """Return the effect instance or create if not exists"""
    if cache:
        cached = cache.get_effect(effect_value)
        if cached:
            return cached
    effect_obj = core.models.Effect.objects.filter(effect__iexact=effect_value).last()
    if effect_obj:
        if cache:
            cache.cache_effect(effect_value, effect_obj)
        return effect_obj
    effect_serializer = core.api.serializers.CreateEffectSerializer(
        data={"effect": effect_value}
    )
    if effect_serializer.is_valid():
        effect_obj = effect_serializer.save()
        if cache:
            cache.cache_effect(effect_value, effect_obj)
        return effect_obj

    return {"ERROR": core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}


def delete_created_variancs(v_in_sample_list, v_an_list):
    for item in v_in_sample_list:
        item.delete()
    for item in v_an_list:
        item.delete()
    return


def store_variant_annotation(v_ann_data, cache=None):
    v_ann_serializer = core.api.serializers.CreateVariantAnnotationSerializer(
        data=v_ann_data
    )
    if not v_ann_serializer.is_valid():
        return {"ERROR": core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}
    v_ann_obj = v_ann_serializer.save()
    if cache:
        cache.cache_annotation(
            v_ann_data.get("hgvs_c"),
            v_ann_data.get("hgvs_p"),
            v_ann_data.get("hgvs_p_1_letter"),
        )
    return v_ann_obj


def store_variant_in_sample(v_data):
    v_in_sample_serializer = core.api.serializers.CreateVariantInSampleSerializer(
        data=v_data
    )
    if not v_in_sample_serializer.is_valid():
        return {"ERROR": core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}
    v_obj = v_in_sample_serializer.save()
    return v_obj


def get_variant_id(data, cache=None):
    """look out for the necessary reference ids to create the variance instance"""
    chromosome = data["chromosome"]
    chr_obj = cache.get_chrom(chromosome) if cache else None
    if chr_obj is None:
        chr_obj = core.utils.variants.get_if_chromosomes_exists(chromosome)
        if cache and chr_obj:
            cache.cache_chrom(chromosome, chr_obj)
    if chr_obj is None:
        return {"ERROR": core.config.ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE}

    pos = str(data["pos"])
    ref = data["ref"]
    alt = data["alt"]

    if cache:
        cached_variant_id = cache.get_variant(chromosome, pos, ref, alt)
        if cached_variant_id:
            return cached_variant_id

    variant_obj = core.models.Variant.objects.filter(
        chromosomeID_id=chr_obj, pos__iexact=pos, alt__iexact=alt
    ).last()
    if variant_obj is None:
        # Create the variant
        filter_obj = create_or_get_filter_obj(data["Filter"], cache=cache)
        if isinstance(filter_obj, dict):
            return filter_obj
        variant_dict = {}
        variant_dict["chromosomeID_id"] = chr_obj.get_chromosome_id()
        variant_dict["filterID_id"] = filter_obj.get_filter_id()
        variant_dict["pos"] = pos
        variant_dict["alt"] = data["alt"]
        variant_dict["ref"] = data["ref"]
        variant_serializer = core.api.serializers.CreateVariantSerializer(
            data=variant_dict
        )
        if not variant_serializer.is_valid():
            return {"ERROR": core.config.ERROR_UNABLE_TO_STORE_IN_DATABASE}
        variant_obj = variant_serializer.save()
    variant_id = variant_obj.get_variant_id()
    if cache:
        cache.cache_variant(chromosome, pos, ref, alt, variant_id)
    return variant_id


def get_variant_analysis_defined(s_obj):
    return core.models.VariantInSample.objects.filter(sampleID_id=s_obj).values_list(
        "bioinformatics_analysis_date", flat=True
    )


def get_required_variant_ann_id(data, cache=None):
    """Look for the ids that variant annotation needs"""
    v_ann_ids = {}
    gene_name = data["gene"]
    gene_obj = cache.get_gene(gene_name) if cache else None
    if gene_obj is None:
        gene_obj = core.utils.variants.get_gene_obj_from_gene_name(gene_name)
        if cache and gene_obj:
            cache.cache_gene(gene_name, gene_obj)

    if gene_obj is None:
        return {"ERROR": core.config.ERROR_GENE_NOT_DEFINED_IN_DATABASE}
    v_ann_ids["geneID_id"] = gene_obj.get_gene_id()
    effect_obj = create_or_get_effect_obj(data["effect"], cache=cache)
    if isinstance(effect_obj, dict):
        return effect_obj
    v_ann_ids["geneID_id"] = gene_obj.get_gene_id()
    v_ann_ids["effectID_id"] = effect_obj.get_effect_id()
    return v_ann_ids


def split_variant_data(data, sample_obj, date, cache=None):
    """Separate the information received into groups"""
    split_data = {"variant_in_sample": {}, "variant_ann": {}}
    split_data["variant_in_sample"]["sampleID_id"] = sample_obj.get_sample_id()

    variant_id = get_variant_id(data, cache=cache)
    if isinstance(variant_id, dict):
        return variant_id
    split_data["variant_in_sample"]["variantID_id"] = variant_id
    split_data["variant_in_sample"]["bioinformatics_analysis_date"] = date

    var_keys = ["dp", "ref_dp", "alt_dp", "af"]
    data["VariantInSample"] = {x: y for x, y in data.items() if x in var_keys}
    split_data["variant_in_sample"].update(data["VariantInSample"])

    v_ann_id = get_required_variant_ann_id(data, cache=cache)
    if "ERROR" in v_ann_id:
        return v_ann_id
    split_data["variant_ann"] = v_ann_id
    split_data["variant_ann"]["variantID_id"] = variant_id

    annot_keys = ["hgvs_c", "hgvs_p", "hgvs_p_1_letter"]
    data["VariantAnnotation"] = {x: y for x, y in data.items() if x in annot_keys}
    split_data["variant_ann"].update(data["VariantAnnotation"])
    return split_data


def variant_annotation_exists(data, cache=None):
    """Check if variant annotation exists. Return True if exists"""
    hgvs_c = data.get("hgvs_c")
    hgvs_p = data.get("hgvs_p")
    hgvs_p1 = data.get("hgvs_p_1_letter")
    if cache and cache.has_annotation(hgvs_c, hgvs_p, hgvs_p1):
        return True
    exists = core.models.VariantAnnotation.objects.filter(
        hgvs_c__iexact=hgvs_c,
        hgvs_p__iexact=hgvs_p,
        hgvs_p_1_letter__iexact=hgvs_p1,
    ).exists()
    if exists and cache:
        cache.cache_annotation(hgvs_c, hgvs_p, hgvs_p1)
    return exists
