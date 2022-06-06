from relecov_core.api.serializers import (
    CreateSampleSerializer,
    CreateChromosomeSerializer,
    CreateGeneSerializer,
    CreateEffectSerializer,
    CreateVariantInSampleSerializer,
    CreateFilterSerializer,
    CreatePositionSerializer,
    CreateVariantSerializer,
)

from relecov_core.models import (
    Sample,
    Chromosome,
    Gene,
    Effect,
    VariantInSample,
    Filter,
    Position,
    Variant,
)


def fetch_long_table_data(data):
    data_ids = {}
    """
    sampleID_id=data_ids["sampleID_id"],
    """

    if Chromosome.objects.filter(chromosome__iexact=data["Chrom"]).exists():
        chrom_id = (
            Chromosome.objects.filter(chromosome__iexact=data["Chrom"])
            .last()
            .get_chromosome_id()
        )
        data_ids["chromosomeID_id"] = chrom_id
        print(chrom_id)
    else:
        chrom_serializer = CreateChromosomeSerializer(data=data["Chrom"])
        # print(chrom_serializer)
        if chrom_serializer.is_valid():
            chrom_serializer.save()
            print("chrom_serializer saved")

    if Gene.objects.filter(gene__iexact=data["Gene"]).exists():
        gene_id = Gene.objects.filter(gene__iexact=data["Gene"]).last().get_gene_id()
        data_ids["geneID_id"] = gene_id
        print(gene_id)
    else:
        gene_serializer = CreateGeneSerializer(data=data["Gene"])
        # print(gene_serializer)
        if gene_serializer.is_valid():
            gene_serializer.save()
            print("gene_serializer saved")

    if Effect.objects.filter(effect__iexact=data["Effect"]).exists():
        effect_id = (
            Effect.objects.filter(effect__iexact=data["Effect"]).last().get_effect_id()
        )
        data_ids["effectID_id"] = effect_id
        print(effect_id)
    else:
        effect_serializer = CreateEffectSerializer(data=data["Effect"])
        # print(effect_serializer)
        if effect_serializer.is_valid():
            effect_serializer.save()
            print("effect_serializer saved")

    if VariantInSample.objects.filter(dp__iexact=data["VariantInSample"]).exists():
        variant_in_sample_id = (
            VariantInSample.objects.filter(effect__iexact=data["VariantInSample"])
            .last()
            .get_variant_in_sample_id()
        )
        data_ids["variant_in_sampleID_id"] = variant_in_sample_id
        print(variant_in_sample_id)
    else:
        variant_in_sample_serializer = CreateVariantInSampleSerializer(
            data=data["VariantInSample"]
        )
        # print(variant_in_sample_serializer)
        if variant_in_sample_serializer.is_valid():
            variant_in_sample_serializer.save()
            print("variant_in_sample_serializer saved")

    if Filter.objects.filter(filter__iexact=data["Filter"]).exists():
        filter_id = (
            Filter.objects.filter(filter__iexact=data["Filter"]).last().get_filter_id()
        )
        data_ids["filterID_id"] = filter_id
        print(filter_id)
    else:
        filter_serializer = CreateFilterSerializer(data=data["Filter"])
        # print(filter_serializer)
        if filter_serializer.is_valid():
            filter_serializer.save()
            print("filter_serializer saved")

    if Position.objects.filter(pos__iexact=data["Position"]).exists():
        position_id = (
            Gene.objects.filter(pos__iexact=data["Position"]).last().get_position_id()
        )
        data_ids["positionID_id"] = position_id
        print(position_id)
    else:
        position_serializer = CreatePositionSerializer(data=data["Position"])
        # print(position_serializer)
        if position_serializer.is_valid():
            position_serializer.save()
            print("position_serializer saved")

    data["sample_id"] = "202134"
    data["sequencing_sample_id"] = "123456"
    data["biosample_accession_ENA"] = "234567"
    data["virus_name"] = "virus name"
    data["gisaid_id"] = "987654"
    sample = Sample.objects.create_new_sample(data, user)
    """
    if Sample.objects.filter(data__iexact=data["Sample"]).exists():
        sample_id = Sample.objects.filter(
            data__iexact=data["Sample"].last().get_sample_id()
        )
        data_ids["sampleID_id"] = sample_id
    else:
        sample_serializer = CreateSampleSerializer(data=data["Sample"])
        if sample_serializer.is_valid():
            sample_serializer.save()
            print("sample_serializer saved")

    if Variant.objects.filter(ref__iexact=data["Variant"]).exists():
        variant_id = (
            Variant.objects.filter(ref__iexact=data["Variant"]).last().get_variant_id()
        )
        print(variant_id)
    else:
        variant = Variant.objects.create_new_variant(data["Variant"], data_ids)
        variant.save()
    """
    """
        variant_serializer = CreateVariantSerializer(data=data["Variant"])
        # print(variant_serializer)
        if variant_serializer.is_valid():
            variant_serializer.save()
            print("variant_serializer saved")
    """
