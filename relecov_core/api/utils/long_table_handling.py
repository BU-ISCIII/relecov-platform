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
    VariantInSample,
    Filter,
    # Position,
    Variant,
    # Document,
    # User,
    # SampleState,
)


def fetch_long_table_data(data):
    data_ids = {}
    sampleID_id = get_sample(data)
    if sampleID_id is not None:
        data_ids["sampleID_id"] = sampleID_id
        for variant in data["variants"]:
            chromosomeID_id = get_chromosome(
                variant["Chromosome"]["chromosome"].split(".")[0]
            )
            if chromosomeID_id is not None:
                data_ids["chromosomeID_id"] = chromosomeID_id

            geneID_id = get_gene(variant["Gene"]["gene"])
            if geneID_id is not None:
                data_ids["geneID_id"] = geneID_id

            effectID_id = set_effect(variant["Effect"])
            if effectID_id is not None:
                data_ids["effectID_id"] = effectID_id

            variant_in_sampleID_id = set_variant_in_sample(variant["VariantInSample"])
            if variant_in_sampleID_id is not None:
                data_ids["variant_in_sampleID_id"] = variant_in_sampleID_id

            filterID_id = set_filter(variant["Filter"])
            if filterID_id is not None:
                data_ids["filterID_id"] = filterID_id

            variantID_id = set_variant(variant["Variant"])
            if variantID_id is not None:
                data_ids["variantID_id"] = variantID_id

            set_variant_annotation(variant["Effect"], data_ids)

    else:
        return {"ERROR": ERROR_SAMPLE_DOES_NOT_EXIST}


def get_chromosome(variant):
    chrom_id = 0

    if Chromosome.objects.filter(chromosome=variant).exists():
        chrom_id = (
            Chromosome.objects.filter(chromosome=variant).last()
            # .get_chromosome_id()
        )

        return chrom_id

    else:
        return {"ERROR": ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE}


"""
def set_caller(data):
    gene_id = 0
    if Gene.objects.filter(gene__iexact=data["Gene"]["gene"]).exists():
        gene_id = Gene.objects.filter(gene__iexact=data["Gene"]["gene"]).last()
        return gene_id
    else:
        return {"ERROR": ERROR_GENE_NOT_DEFINED_IN_DATABASE}
"""


def get_gene(gene):
    gene_id = 0
    if Gene.objects.filter(gene_name__iexact=gene).exists():
        gene_id = Gene.objects.filter(gene_name__iexact=gene).last()
        return gene_id
    else:
        return {"ERROR": ERROR_GENE_NOT_DEFINED_IN_DATABASE}


def set_effect(effect):
    effect_id = 0
    if Effect.objects.filter(effect__iexact=effect["effect"]).exists():
        effect_id = (
            Effect.objects.filter(effect__iexact=effect["effect"]).last()
            # .get_effect_id()
        )
        return effect_id
    else:
        effect_serializer = CreateEffectSerializer(data=effect)
        if effect_serializer.is_valid():
            effect_serializer.save()


def set_variant_in_sample(variant_in_sample):
    variant_in_sample_id = 0
    if VariantInSample.objects.filter(dp__iexact=variant_in_sample["dp"]).exists():
        variant_in_sample_id = (
            VariantInSample.objects.filter(dp__iexact=variant_in_sample["dp"]).last()
            # .get_variant_in_sample_id()
        )
        return variant_in_sample_id
    else:
        variant_in_sample_serializer = CreateVariantInSampleSerializer(
            data=variant_in_sample
        )
        if variant_in_sample_serializer.is_valid():
            variant_in_sample_serializer.save()


def set_filter(filter):
    filter_id = 0
    if Filter.objects.filter(filter__iexact=filter["filter"]).exists():
        filter_id = (
            Filter.objects.filter(filter__iexact=filter["filter"]).last()
            # .get_filter_id()
        )
        return filter_id
    else:
        filter_serializer = CreateFilterSerializer(data=filter)
        if filter_serializer.is_valid():
            filter_serializer.save()


def set_variant_annotation(effect, data_ids):
    data = {}

    data["variantID_id"] = data_ids["variantID_id"]
    data["geneID_id"] = data_ids["geneID_id"]
    data["effectID_id"] = data_ids["effectID_id"]
    data["hgvs_c"] = effect["hgvs_c"]
    data["hgvs_p"] = effect["hgvs_p"]
    data["hgvs_p_1letter"] = effect["hgvs_p_1letter"]

    variant_annotation = CreateVariantAnnotationSerializer(data=data)
    if variant_annotation.is_valid():
        variant_annotation.save()

    """
    if Variant.objects.filter(pos__iexact=data["variants"]["Position"]["pos"]).exists():
        variantID_id = (
            Variant.objects.filter(
                pos__iexact=data["variants"]["Position"]["pos"]
            ).last()
            # .get_position_id()
        )
        return variantID_id
    else:
        data_to_serializer["Position"]["pos"] = data["variants"]["Position"]["pos"]
        data_to_serializer["Position"]["nucleotide"] = data["variants"]["Position"][
            "nucleotide"
        ]
        variant_serializer = CreateVariantSerializer(data=data_to_serializer)
        if variant_serializer.is_valid():
            variant_serializer.save()
    """


def get_sample(data):
    sample_id = 0
    if Sample.objects.filter(sequencing_sample_id=data["sample"]).exists():
        sample_id = Sample.objects.filter(sequencing_sample_id=data["sample"]).last()

        return sample_id

    else:
        return {"ERROR": ERROR_SAMPLE_DOES_NOT_EXIST}


def set_variant(variant):
    if Variant.objects.filter(ref__iexact=variant["ref"]).exists():
        variant_id = (
            Variant.objects.filter(ref__iexact=variant["ref"]).last()
            # .get_variant_id()
        )
        return variant_id
    else:
        variant_serializer = CreateVariantSerializer(data=variant)
        if variant_serializer.is_valid():
            variant_serializer.save()

        """
        variant_serializer = CreateVariantSerializer(data=data["Variant"])
        print(variant_serializer)
        if variant_serializer.is_valid():
            variant_serializer.save()
            print("variant_serializer saved")
        """


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
"""
