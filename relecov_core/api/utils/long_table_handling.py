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
    Document,
    User,
    SampleState,
)


def fetch_long_table_data(data):
    # create_sample_register()

    data_ids = {}
    for idx in range(2):
        chromosomeID_id = set_chromosome(data)
        if chromosomeID_id is not None:
            data_ids["chromosomeID_id"] = chromosomeID_id

        geneID_id = set_gene(data)
        if geneID_id is not None:
            data_ids["geneID_id"] = geneID_id

        effectID_id = set_effect(data)
        if effectID_id is not None:
            data_ids["effectID_id"] = effectID_id

        variant_in_sampleID_id = set_variant_in_sample(data)
        if variant_in_sampleID_id is not None:
            data_ids["variant_in_sampleID_id"] = variant_in_sampleID_id

        filterID_id = set_filter(data)
        if filterID_id is not None:
            data_ids["filterID_id"] = filterID_id

        positionID_id = set_position(data)
        if positionID_id is not None:
            data_ids["positionID_id"] = positionID_id

        # print(chromosomeID_id)
        # print(geneID_id)
        print(effectID_id)

    sampleID_id = set_sample(data)
    if sampleID_id is not None:
        data_ids["sampleID_id"] = sampleID_id

    print(data_ids)

    variantID_id = set_variant(data, data_ids)
    if variantID_id is not None:
        data_ids["variantID_id"] = variantID_id


def set_chromosome(data):
    chrom_id = 0
    print(
        Chromosome.objects.filter(
            chromosome__iexact=data["Chrom"]["chromosome"]
        ).exists()
    )
    print(data["Chrom"]["chromosome"])
    if Chromosome.objects.filter(chromosome=data["Chrom"]["chromosome"]).last():
        chrom_id = (
            Chromosome.objects.filter(chromosome=data["Chrom"]["chromosome"]).last()
            # .get_chromosome_id()
        )

        return chrom_id

    else:
        chrom_serializer = CreateChromosomeSerializer(data=data["Chrom"])
        if chrom_serializer.is_valid():
            chrom_serializer.save()
            print("chrom_serializer saved")


def set_gene(data):
    gene_id = 0
    if Gene.objects.filter(gene__iexact=data["Gene"]["gene"]).exists():
        gene_id = (
            Gene.objects.filter(gene__iexact=data["Gene"]["gene"]).last()
            # .get_gene_id()
        )
        # data_ids["geneID_id"] = gene_id
        return gene_id
    else:
        gene_serializer = CreateGeneSerializer(data=data["Gene"]["gene"])
        # print(gene_serializer)
        if gene_serializer.is_valid():
            gene_serializer.save()
            print("gene_serializer saved")


def set_effect(data):
    effect_id = 0
    if Effect.objects.filter(effect__iexact=data["Effect"]["effect"]).exists():
        effect_id = (
            Effect.objects.filter(effect__iexact=data["Effect"]["effect"]).last()
            # .get_effect_id()
        )
        # data_ids["effectID_id"] = effect_id
        return effect_id
    else:
        effect_serializer = CreateEffectSerializer(data=data["Effect"])
        # print(effect_serializer)
        if effect_serializer.is_valid():
            effect_serializer.save()
            print("effect_serializer saved")


def set_variant_in_sample(data):
    variant_in_sample_id = 0
    if VariantInSample.objects.filter(
        dp__iexact=data["VariantInSample"]["dp"]
    ).exists():
        variant_in_sample_id = (
            VariantInSample.objects.filter(
                dp__iexact=data["VariantInSample"]["dp"]
            ).last()
            # .get_variant_in_sample_id()
        )
        # data_ids["variant_in_sampleID_id"] = variant_in_sample_id
        return variant_in_sample_id
    else:
        variant_in_sample_serializer = CreateVariantInSampleSerializer(
            data=data["VariantInSample"]
        )
        # print(variant_in_sample_serializer)
        if variant_in_sample_serializer.is_valid():
            variant_in_sample_serializer.save()
            print("variant_in_sample_serializer saved")


def set_filter(data):
    filter_id = 0
    if Filter.objects.filter(filter__iexact=data["Filter"]["filter"]).exists():
        filter_id = (
            Filter.objects.filter(filter__iexact=data["Filter"]["filter"]).last()
            # .get_filter_id()
        )
        # data_ids["filterID_id"] = filter_id
        return filter_id
    else:
        filter_serializer = CreateFilterSerializer(data=data["Filter"])
        # print(filter_serializer)
        if filter_serializer.is_valid():
            filter_serializer.save()
            print("filter_serializer saved")


def set_position(data):
    position_id = 0
    if Position.objects.filter(pos__iexact=data["Position"]["pos"]).exists():
        position_id = (
            Position.objects.filter(pos__iexact=data["Position"]["pos"]).last()
            # .get_position_id()
        )
        # data_ids["positionID_id"] = position_id
        return position_id
    else:
        position_serializer = CreatePositionSerializer(data=data["Position"])
        # print(position_serializer)
        if position_serializer.is_valid():
            position_serializer.save()
            print("position_serializer saved")


def set_sample(data):
    sample_id = 0
    if Sample.objects.filter(
        collecting_lab_sample_id=data["Sample"]["collecting_lab_sample_id"]
    ).exists():
        sample_id = (
            Sample.objects.filter(
                collecting_lab_sample_id=data["Sample"]["collecting_lab_sample_id"]
            ).last()
            # .get_sample_id()
        )

        # data_ids["sampleID_id"] = sample_id
        return sample_id
    """
    else:
        sample_serializer = CreateSampleSerializer(data=data["Sample"])
        if sample_serializer.is_valid():
            sample_serializer.save()
            print("sample_serializer saved")
    """


def set_variant(data, data_ids):
    if Variant.objects.filter(ref__iexact=data["Variant"]["ref"]).exists():
        variant_id = (
            Variant.objects.filter(ref__iexact=data["Variant"]["ref"])
            .last()
            .get_variant_id()
        )
        print(variant_id)
    else:
        variant = Variant.objects.create_new_variant(data["Variant"]["ref"], data_ids)
        variant.save()

        """
        variant_serializer = CreateVariantSerializer(data=data["Variant"])
        print(variant_serializer)
        if variant_serializer.is_valid():
            variant_serializer.save()
            print("variant_serializer saved")
        """


# this function creates a new Sample register for testing
def create_sample_register():
    new_sample = Sample.objects.create(
        state=SampleState.objects.create(
            state="pre-recorded",
            display_string="display_string",
            description="description",
        ),
        user=User.objects.create(password="appapk", username="tere"),
        metadata_file=Document.objects.create(
            title="title", file_path="", uploadedFile=""
        ),
        collecting_lab_sample_id="200002",
        sequencing_sample_id="1234",
        biosample_accession_ENA="456123",
        virus_name="ramiro",
        gisaid_id="09876",
        sequencing_date="2022/8/2",
    )
    new_sample.save()
