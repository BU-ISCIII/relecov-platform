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
    import pdb

    data_ids = {}
    sample_obj = get_sample(data)

    # Check if sample exists
    if sample_obj is not None:
        data_ids["sampleID_id"] = sample_obj.get_sample_id()
        # for variant in data["variants"]:
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

            variant_annotation_obj = set_variant_annotation(variant["Effect"], data_ids)
            if variant_annotation_obj is not None:
                data_ids[
                    "variant_annotationID_id"
                ] = variant_annotation_obj.get_variant_annotation_id()

            variant_obj = set_variant(variant["Variant"], variant["Position"], data_ids)
            if variant_obj is not None:
                data_ids["variantID_id"] = variant_obj.get_variant_id()

        pdb.set_trace()
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
    effect_id = 0
    if Effect.objects.filter(effect__iexact=effect["effect"]).exists():
        effect_id = Effect.objects.filter(effect__iexact=effect["effect"]).last()
        return effect_id
    else:
        effect_serializer = CreateEffectSerializer(data=effect)
        if effect_serializer.is_valid():
            effect_serializer.save()


def set_variant_in_sample(variant_in_sample, data_ids):
    variant_in_sample_id = 0
    if VariantInSample.objects.filter(dp__iexact=variant_in_sample["dp"]).exists():
        variant_in_sample_id = VariantInSample.objects.filter(
            dp__iexact=variant_in_sample["dp"]
        ).last()
        return variant_in_sample_id
    else:
        variant_in_sample["sampleID_id"] = data_ids["sampleID_id"]
        variant_in_sample["filterID_id"] = data_ids["filterID_id"]
        variant_in_sample_serializer = CreateVariantInSampleSerializer(
            data=variant_in_sample
        )
        if variant_in_sample_serializer.is_valid():
            variant_in_sample_serializer.save()


def set_filter(filter):
    import pdb

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
    else:
        filter_serializer = CreateFilterSerializer(data=filter)
        if filter_serializer.is_valid():
            filter_serializer.save()
            return return_filter_obj(filter_string=filter)
    pdb.set_trace()
    """
    filter_id = 0
    if Filter.objects.filter(filter__iexact=filter["filter"]).exists():
        filter_id = Filter.objects.filter(filter__iexact=filter["filter"]).last()
        return filter_id
    else:
        filter_serializer = CreateFilterSerializer(data=filter)
        if filter_serializer.is_valid():
            filter_serializer.save()
    """


def set_variant_annotation(effect, data_ids):
    # import pdb
    if VariantAnnotation.objects.filter(geneID_id=data_ids["geneID_id"]).exists():
        variant_annotation_id = VariantAnnotation.objects.filter(
            geneID_id=data_ids["geneID_id"]
        ).last()
        return variant_annotation_id
    else:
        data = {}

        # data["variantID_id"] = data_ids["variantID_id"]
        data["geneID_id"] = data_ids["geneID_id"]
        # data["effectID_id"] = data_ids["effectID_id"]
        data["hgvs_c"] = effect["hgvs_c"]
        data["hgvs_p"] = effect["hgvs_p"]
        data["hgvs_p_1letter"] = effect["hgvs_p_1_letter"]

        # print(data)
        # pdb.set_trace()
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


def set_variant(variant, position, data_ids):
    if Variant.objects.filter(ref__iexact=variant["ref"]).exists():
        variant_id = Variant.objects.filter(ref__iexact=variant["ref"]).last()
        return variant_id
    else:
        data = {}
        data["chromosomeID_id"] = data_ids["chromosomeID_id"]
        data["geneID_id"] = data_ids["geneID_id"]
        data["variant_annotationID_id"] = data_ids["variant_annotationID_id"]
        data["effectID_id"] = data_ids["effectID_id"]
        data["filterID_id"] = data_ids["filterID_id"]
        data["variant_in_sampleID_id"] = data_ids["variant_in_sampleID_id"]
        data["ref"] = variant["ref"]
        data["pos"] = position["pos"]
        data["alt"] = position["alt"]

        variant_serializer = CreateVariantSerializer(data=data)
        if variant_serializer.is_valid():
            variant_serializer.save()

        """
        chromosomeID_id = models.ForeignKey(Chromosome, on_delete=models.CASCADE)
    effectID_id = models.ForeignKey(Effect, on_delete=models.CASCADE)
    callerID_id = models.ForeignKey(Caller, on_delete=models.CASCADE)
    filterID_id = models.ForeignKey(Filter, on_delete=models.CASCADE)
    variant_in_sampleID_id = models.ForeignKey(
        VariantInSample, on_delete=models.CASCADE
    )
    # af = models.CharField(max_length=6)
    # alt_dp = models.CharField(max_length=5)
    ref = models.CharField(max_length=60)
    pos = models.CharField(max_length=60)
    alt = models.CharField(max_length=100)
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
