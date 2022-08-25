from relecov_core.api.serializers import (
    # CreateChromosomeSerializer,
    # CreateGeneSerializer,
    CreateEffectSerializer,
    CreateVariantInSampleSerializer,
    CreateVariantAnnotationSerializer,
    CreateFilterSerializer,
    # CreatePositionSerializer,
    # CreateLineageSerializer,
    CreateVariantSerializer,
)
from relecov_core.core_config import (
    ERROR_SAMPLE_DOES_NOT_EXIST,
    ERROR_GENE_NOT_DEFINED_IN_DATABASE,
    ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE,
)

from relecov_core.models import (
    Sample,
    Chromosome,
    Gene,
    Effect,
    VariantAnnotation,
    VariantInSample,
    Filter,
    # Position,
    Variant,
    # Document,
    # User,
    # SampleState,
)


def fetch_long_table_data(data):
    # import pdb
    data_ids = {}
    sample_obj = get_sample(data)

    # Check if sample exists
    if sample_obj is not None:
        data_ids["sampleID_id"] = sample_obj.get_sample_id()
        for idx in range(len(data["variants"])):
            variant = data["variants"][idx]
            chromosome_obj = get_chromosome(
                variant["Chromosome"]["chromosome"].split(".")[0]
            )
            if chromosome_obj is not None:
                data_ids["chromosomeID_id"] = chromosome_obj.get_chromosome_id()

            gene_obj = get_gene(variant["Gene"]["gene"])
            if gene_obj is not None:
                data_ids["geneID_id"] = gene_obj.get_gene_id()

            effect_obj = set_effect(variant["Effect"])
            if effect_obj is not None:
                data_ids["effectID_id"] = effect_obj.get_effect_id()

            filter_obj = set_filter(variant["Filter"])
            if filter_obj is not None:
                data_ids["filterID_id"] = filter_obj.get_filter_id()

            variant_in_sample_obj = set_variant_in_sample(
                variant["VariantInSample"], data_ids
            )
            if variant_in_sample_obj is not None:
                data_ids[
                    "variant_in_sampleID_id"
                ] = variant_in_sample_obj.get_variant_in_sample_id()

            variant_obj = set_variant(
                data, variant["Variant"], variant["Position"], data_ids
            )
            if variant_obj is not None:
                data_ids["variantID_id"] = variant_obj.get_variant_id()

            # pdb.set_trace()

            variant_annotation_obj = set_variant_annotation(variant["Effect"], data_ids)
            if variant_annotation_obj is not None:
                variant_annotation_obj.variantID_id.add(variant_obj)
                data_ids[
                    "variant_annotationID_id"
                ] = variant_annotation_obj.get_variant_annotation_id()

        return {"SUCCESS": "Success"}

    else:
        return {"ERROR": ERROR_SAMPLE_DOES_NOT_EXIST}


def get_chromosome(variant):
    chrom_id = 0

    if Chromosome.objects.filter(chromosome=variant).exists():
        chrom_id = Chromosome.objects.filter(chromosome=variant).last()

        return chrom_id

    else:
        return {"ERROR": ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE}


def get_gene(gene):
    gene_id = 0
    if Gene.objects.filter(gene_name__iexact=gene).exists():
        gene_id = Gene.objects.filter(gene_name__iexact=gene).last()
        return gene_id
    else:
        return {"ERROR": ERROR_GENE_NOT_DEFINED_IN_DATABASE}


def set_effect(effect):
    def return_effect_obj(effect):
        effect_obj = 0
        if Effect.objects.filter(
            effect__iexact=effect["effect"],
        ).exists():
            effect_obj = Effect.objects.filter(effect__iexact=effect["effect"]).last()
            return effect_obj
        else:
            return None

    effect_obj = 0
    if return_effect_obj(effect) is not None:
        effect_obj = return_effect_obj(effect)
        return effect_obj
    else:
        effect_serializer = CreateEffectSerializer(data=effect)
        if effect_serializer.is_valid():
            effect_serializer.save()
            return return_effect_obj(effect)


def set_variant_in_sample(variant_in_sample, data_ids):
    def return_variant_in_sample(variant_in_sample, data_ids):
        variant_in_sample_obj = 0
        if VariantInSample.objects.filter(
            sampleID_id=data_ids["sampleID_id"],
            dp__iexact=variant_in_sample["dp"],
            ref_dp__iexact=variant_in_sample["ref_dp"],
            alt_dp__iexact=variant_in_sample["alt_dp"],
            af__iexact=variant_in_sample["af"],
        ).exists():
            variant_in_sample_obj = VariantInSample.objects.filter(
                sampleID_id=data_ids["sampleID_id"],
                dp__iexact=variant_in_sample["dp"],
                ref_dp__iexact=variant_in_sample["ref_dp"],
                alt_dp__iexact=variant_in_sample["alt_dp"],
                af__iexact=variant_in_sample["af"],
            ).last()
            return variant_in_sample_obj
        else:
            return None

    def create_variant_in_sample_dict(variant_in_sample_dict, data_ids):
        data = {}
        data["sampleID_id"] = data_ids["sampleID_id"]
        data["filterID_id"] = data_ids["filterID_id"]
        data["dp"] = variant_in_sample_dict["dp"]
        data["ref_dp"] = variant_in_sample_dict["ref_dp"]
        data["alt_dp"] = variant_in_sample_dict["alt_dp"]
        data["af"] = variant_in_sample_dict["af"]

        return data

    variant_in_sample_obj = 0
    if return_variant_in_sample(variant_in_sample, data_ids) is not None:
        variant_in_sample_obj = return_variant_in_sample(variant_in_sample, data_ids)
        return variant_in_sample_obj
    else:
        data = create_variant_in_sample_dict(variant_in_sample, data_ids)
        variant_in_sample_serializer = CreateVariantInSampleSerializer(data=data)
        if variant_in_sample_serializer.is_valid():
            variant_in_sample_serializer.save()
            return return_variant_in_sample(variant_in_sample, data_ids)


def set_filter(filter):
    def return_filter_obj(filter_string):
        filter_obj = 0
        if Filter.objects.filter(filter__iexact=filter_string["filter"]).exists():
            filter_obj = Filter.objects.filter(
                filter__iexact=filter_string["filter"]
            ).last()
            return filter_obj
        else:
            return None

    filter_obj = 0
    if return_filter_obj(filter_string=filter) is not None:
        filter_obj = return_filter_obj(filter_string=filter)
        return filter_obj
    # create register and return created register
    else:
        filter_serializer = CreateFilterSerializer(data=filter)
        if filter_serializer.is_valid():
            filter_serializer.save()
            return return_filter_obj(filter_string=filter)


def set_variant_annotation(effect, data_ids):
    def return_variant_annotation_obj(effect, data_ids):
        variant_annotation_obj = 0
        if VariantAnnotation.objects.filter(geneID_id=data_ids["geneID_id"]).exists():
            variant_annotation_obj = VariantAnnotation.objects.filter(
                geneID_id=data_ids["geneID_id"]
            ).last()
            return variant_annotation_obj
        else:
            return None

    def create_variant_annotation_dict(effect, data_ids):
        data = {}
        data["geneID_id"] = data_ids["geneID_id"]
        data["effectID_id"] = data_ids["effectID_id"]
        data["hgvs_c"] = effect["hgvs_c"]
        data["hgvs_p"] = effect["hgvs_p"]
        data["hgvs_p_1letter"] = effect["hgvs_p_1_letter"]
        data["variantID_id"] = data_ids["variantID_id"]

        return data

    if return_variant_annotation_obj(effect, data_ids) is not None:
        variant_annotation_obj = return_variant_annotation_obj(effect, data_ids)
        return variant_annotation_obj
    else:
        data = create_variant_annotation_dict(effect, data_ids)

        variant_annotation = CreateVariantAnnotationSerializer(data=data)
        if variant_annotation.is_valid():
            variant_annotation.save()
            return return_variant_annotation_obj(effect, data_ids)


def get_sample(data):
    sample_id = 0
    if Sample.objects.filter(sequencing_sample_id=data["sample"]).exists():
        sample_id = Sample.objects.filter(sequencing_sample_id=data["sample"]).last()

        return sample_id

    else:
        return {"ERROR": ERROR_SAMPLE_DOES_NOT_EXIST}


def set_variant(data, variant, position, data_ids):
    def check_if_sample_has_same_pos_and_alt(data, variant, position, data_ids):
        if Sample.objects.filter(sequencing_sample_id=data["sample"]).exists():
            sample_obj_check = Sample.objects.filter(
                sequencing_sample_id=data["sample"]
            ).last()
            print("sample_obj_check: ")
            print(sample_obj_check)
            if VariantInSample.objects.filter(sampleID_id=sample_obj_check).exists():
                variant_in_sample_objs_check = VariantInSample.objects.filter(
                    sampleID_id=sample_obj_check
                )  # .last().get_variant_in_sample_id()
                print("variant_in_sample_objs_check")
                print(variant_in_sample_objs_check)
                for variant_obj in variant_in_sample_objs_check:
                    print(variant_obj.get_variant_in_sample_id())

                    if Variant.objects.filter(
                        variant_in_sampleID_id=variant_obj.get_variant_in_sample_id(),
                        pos=position["pos"],
                        alt=position["alt"],
                    ).exists():
                        variant_obj_check = Variant.objects.filter(
                            variant_in_sampleID_id=variant_obj.get_variant_in_sample_id(),
                            pos=position["pos"],
                            alt=position["alt"],
                        ).last()
                        return variant_obj_check
                    else:
                        return None

    variant_obj_check = check_if_sample_has_same_pos_and_alt(
        data, variant, position, data_ids
    )
    print("variant_obj_check")
    print(variant_obj_check)
    if variant_obj_check is not None:
        print("return variant_obj_check")
        return variant_obj_check

    else:
        data = {}
        data["chromosomeID_id"] = data_ids["chromosomeID_id"]
        data["filterID_id"] = data_ids["filterID_id"]
        data["variant_in_sampleID_id"] = data_ids["variant_in_sampleID_id"]
        data["ref"] = variant["ref"]
        data["pos"] = position["pos"]
        data["alt"] = position["alt"]
        # data["geneID_id"] = data_ids["geneID_id"]
        # data["variant_annotationID_id"] = data_ids["variant_annotationID_id"]
        # data["effectID_id"] = data_ids["effectID_id"]

        variant_serializer = CreateVariantSerializer(data=data)
        if variant_serializer.is_valid():
            variant_serializer.save()
            print("variant_serializer.save()")
