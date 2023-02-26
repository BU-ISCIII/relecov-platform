from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from rest_framework import status
from rest_framework.response import Response

# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi

from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    inline_serializer,
    OpenApiResponse,
)
from rest_framework import serializers

from django.http import QueryDict
from relecov_core.api.serializers import (
    CreateDateAfterChangeStateSerializer,
    CreateSampleSerializer,
    CreateErrorSerializer,
    UpdateStateSampleSerializer,
)

from relecov_core.models import SampleState, Error


from relecov_core.api.utils.sample_handling import (
    split_sample_data,
)
from relecov_core.utils.handling_samples import get_sample_obj_from_sample_name

from relecov_core.api.utils.bioinfo_metadata_handling import (
    split_bioinfo_data,
    store_bioinfo_data,
    get_analysis_defined,
)

from relecov_core.api.utils.public_db_handling import store_pub_databases_data

from relecov_core.api.utils.variant_handling import (
    split_variant_data,
    store_variant_annotation,
    store_variant_in_sample,
    delete_created_variancs,
    variant_annotation_exists,
    get_variant_analysis_defined,
)

from relecov_core.api.utils.common_functions import (
    get_schema_version_if_exists,
    update_change_state_date,
)

from relecov_core.core_config import (
    ERROR_SAMPLE_NAME_NOT_INCLUDED,
    ERROR_SAMPLE_NOT_DEFINED,
    ERROR_VARIANT_INFORMATION_NOT_DEFINED,
    ERROR_ANALYSIS_ALREADY_DEFINED,
)

"""
@swagger_auto_schema(
    method="post",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "analysis_authors": openapi.Schema(
                type=openapi.TYPE_STRING, description="Author of the analysis"
            ),
            "author_submitter": openapi.Schema(
                type=openapi.TYPE_STRING, description="Submitter author to GISAID"
            ),
            "authors": openapi.Schema(
                type=openapi.TYPE_STRING, description="Authors involved in the analysis"
            ),
            "experiment_alias": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Experiment alias used for uploading to ENA",
            ),
            "experiment_title": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Experiment title for uploading to ENA",
            ),
            "fastq_r1_md5": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="MD5 for fastq R1 file",
            ),
            "fastq_r2_md5": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="MD5 for fastq R2 file",
            ),
            "gisaid_id": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Id given by GISAID",
            ),
            "microbiology_lab_sample_id": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Sample name ID given by the microbiology lab ",
            ),
            "r1_fastq_filepath": openapi.Schema(
                type=openapi.TYPE_STRING, description="Path where fastq R1 is stored"
            ),
            "r2_fastq_filepath": openapi.Schema(
                type=openapi.TYPE_STRING, description="Path where fastq R2 is stored"
            ),
            "sequence_file_R1_fastq": openapi.Schema(
                type=openapi.TYPE_STRING, description="File name of fastq R1"
            ),
            "sequence_file_R2_fastq": openapi.Schema(
                type=openapi.TYPE_STRING, description="File name of fastq R2"
            ),
            "sequencing_sample_id": openapi.Schema(
                type=openapi.TYPE_STRING, description="Project name"
            ),
            "study_alias": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Study alias used for uplading to ENA",
            ),
            "study_id": openapi.Schema(
                type=openapi.TYPE_STRING, description="Study ID for uploading to ENA"
            ),
            "study_title": openapi.Schema(
                type=openapi.TYPE_STRING, description="Study title for uploading to ENA"
            ),
            "study_type": openapi.Schema(
                type=openapi.TYPE_STRING, description="Study type for uploading to ENA"
            ),
            "submitting_lab_sample_id": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="sample name id given by the submitted lab",
            ),
        },
    ),
    responses={
        201: "Successful create information",
        400: "Bad Request",
        500: "Internal Server Error",
    },
)
    
    responses={
        200: inline_serializer(
           name='samples',
           fields={
               'title2': serializers.CharField(),
           }
        )
    }
    examples=[OpenApiExample(
        "Example-1",
        description="des",
        value=[
            {'analysis_authors': 'Bob Robert'},
            {'submitting_lab_sample_id': 'Another title'},
            {'submitting_lab_sample_id': 'Another title'},
        ],
    ), OpenApiExample("Exaple-2", description="ese", 
                    value= [{"par2":"res"}])
    ],
"""
"""
    parameters=[
        OpenApiParameter(name="analysis_authors", description="Authors of the analysis", required=False, type=str),
        OpenApiParameter(name="author_submitter", description="Author that submit to GISAID", required=False, type=str),
        OpenApiParameter(name="authors", description="Author involved in the Analysis", required=False, type=str),
        OpenApiParameter(name="experiment_alias", description="Experiment alias used for uploading to ENA", required=False, type=str),
        OpenApiParameter(name="experiment_title", description="Experiment title for uploading to ENA", required=False, type=str),
        OpenApiParameter(name="fastq_r1_md5", description="MD5 for fastq R1 file", required=False, type=str),
        OpenApiParameter(name="fastq_r2_md5", description="MD5 for fastq R2 file", required=False, type=str),
        OpenApiParameter(name="gisaid_id", description="Id given by GISAID", required=False, type=str),
        OpenApiParameter(name="microbiology_lab_sample_id", description="Sample name ID given by the microbiology lab", required=False, type=str),
        OpenApiParameter(name="r1_fastq_filepath", description="Path where fastq R1 is stored", required=False, type=str),
        OpenApiParameter(name="r2_fastq_filepath", description="Path where fastq R2 is stored", required=False, type=str),
        OpenApiParameter(name="schema_name", description="Name of the Schema. (Relecov)", required=True, type=str),
        OpenApiParameter(name="schema_version", description="Version of the Schema. ", required=True, type=str),
        OpenApiParameter(name="sequence_file_R1_fastq", description="File name of fastq R1", required=False, type=str),
        OpenApiParameter(name="sequence_file_R2_fastq", description="File name of fastq R2", required=False, type=str),
        OpenApiParameter(name="sequencing_sample_id", description="Sample ID used in seqencing", required=True, type=str),
        OpenApiParameter(name="study_alias", description="Study alias used for uplading to ENA", required=False, type=str),
        OpenApiParameter(name="study_id", description="Study ID for uploading to ENA", required=False, type=str),
        OpenApiParameter(name="study_title", description="Study title for uploading to ENA", required=False, type=str),
        OpenApiParameter(name="study_type", description="Study type for uploading to ENA", required=False, type=str),
        OpenApiParameter(name="submitting_lab_sample_id", description="Sample name id given by the submitted lab", required=True, type=str),
    ],
"""
"""
@extend_schema(
    request=CreateSampleSerializer,
    responses={201: OpenApiResponse(description="Successful upload information")},
)
"""

@extend_schema(
    request=inline_serializer(
        name="createSample",
        fields={
            "analysis_authors": serializers.CharField(),
            "author_submitter": serializers.CharField(),
            "authors": serializers.CharField(),
            "experiment_alias": serializers.CharField(),
            "experiment_title": serializers.CharField(),
            "fastq_r1_md5": serializers.CharField(),
            "fastq_r2_md5": serializers.CharField(),
            "gisaid_id": serializers.CharField(),
            "microbiology_lab_sample_id": serializers.CharField(),
            "r1_fastq_filepath": serializers.CharField(),
            "r2_fastq_filepath": serializers.CharField(),
            "schema_name": serializers.CharField(),
            "schema_version": serializers.CharField(),
            "sequence_file_R1_fastq": serializers.CharField(),
            "sequence_file_R2_fastq": serializers.CharField(),
            "sequencing_sample_id": serializers.CharField(),
            "study_alias": serializers.CharField(),
            "study_id": serializers.CharField(),
            "study_title": serializers.CharField(),
            "study_type": serializers.CharField(),
            "submitting_lab_sample_id": serializers.CharField(),
        },
    ),
    description="More descriptive text",
    responses={
        201: OpenApiResponse(description="Successful upload information"),
        400: OpenApiResponse(description="Bad request"),
        500: OpenApiResponse(description="Internal Server Error"),
    },
)
@authentication_classes([SessionAuthentication, BasicAuthentication])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_sample_data(request):
    if request.method == "POST":
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()

        schema_obj = get_schema_version_if_exists(data)
        if schema_obj is None:
            error = {"ERROR": "schema name and version is not defined"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        schema_id = schema_obj.get_schema_id()
        # check if sample id field and collecting_institution are in the request
        if "sequencing_sample_id" not in data or "collecting_institution" not in data:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        # check if sample is already defined
        if get_sample_obj_from_sample_name(data["sequencing_sample_id"]):
            error = {"ERROR": "sample already defined"}
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        # get the user to assign the sample based on the collecting_institution
        # value. If lab is not define user field is set t
        split_data = split_sample_data(data)
        # Add schema id to store in databasee
        split_data["sample"]["schema_obj"] = schema_id
        sample_serializer = CreateSampleSerializer(data=split_data["sample"])
        if not sample_serializer.is_valid():
            return Response(
                sample_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        sample_obj = sample_serializer.save()
        sample_id = sample_obj.get_sample_id()
        # update sample state date
        data = {
            "sampleID": sample_id,
            "stateID": split_data["sample"]["state"],
        }
        date_serilizer = CreateDateAfterChangeStateSerializer(data=data)
        if date_serilizer.is_valid():
            date_serilizer.save()

        # Save ENA info if included
        if len(split_data["ena"]) > 0:
            if (
                split_data["ena"]["ena_sample_accession"] != "Not Provided"
                and split_data["ena"]["ena_sample_accession"] != ""
            ):
                result = store_pub_databases_data(
                    split_data["ena"], "ena", schema_obj, sample_id
                )
                if "ERROR" in result:
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
                # Save entry in update state table
                sample_obj.update_state("Ena")
                state_id = (
                    SampleState.objects.filter(state__exact="Ena").last().get_state_id()
                )
                data = {"sampleID": sample_id, "stateID": state_id}
                date_serilizer = CreateDateAfterChangeStateSerializer(data=data)
                if date_serilizer.is_valid():
                    date_serilizer.save()
        # Save GISAID info if included
        if len(split_data["gisaid"]) > 0:
            if "EPI_ISL" in split_data["gisaid"]["gisaid_accession_id"]:
                result = store_pub_databases_data(
                    split_data["gisaid"], "gisaid", schema_obj, sample_id
                )
                if "ERROR" in result:
                    return Response(result, status=status.HTTP_400_BAD_REQUEST)
                # Save entry in update state table
                sample_obj.update_state("Gisaid")
                state_id = (
                    SampleState.objects.filter(state__exact="Gisaid")
                    .last()
                    .get_state_id()
                )
                data = {"sampleID": sample_id, "stateID": state_id}
                date_serilizer = CreateDateAfterChangeStateSerializer(data=data)
                if date_serilizer.is_valid():
                    date_serilizer.save()
        # Save AUTHOR info if included
        if len(split_data["author"]) > 0:
            result = store_pub_databases_data(
                split_data["author"], "author", schema_obj, sample_id
            )
            if "ERROR" in result:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
        return Response("Successful upload information", status=status.HTTP_201_CREATED)


""""
@extend_schema(
    parameters=[
        OpenApiParameter(name="", description="The time of a sample analysis process", required=False, type=str),
        OpenApiParameter(name="assembly", description="Software used for assembly of the pathogen genome.", required=False, type=str),
        OpenApiParameter(name="assembly_params", description="Params used for genome assembly.", required=False, type=str),
        OpenApiParameter(name="bioinformatics_protocol_software_name", description="The name  of the bioinformatics protocol used.", required=False, type=str),
        OpenApiParameter(name="bioinformatics_protocol_software_version", description="", required=False, type=str),
        OpenApiParameter(name="commercial_open_source_both", description="", required=False, type=str),
        OpenApiParameter(name="consensus_genome_length", description="", required=False, type=str),
        OpenApiParameter(name="consensus_params", description="", required=False, type=str),
        OpenApiParameter(name="consensus_sequence_filename", description="", required=False, type=str),
        OpenApiParameter(name="consensus_sequence_filepath", description="", required=False, type=str),
        OpenApiParameter(name="consensus_sequence_md5", description="", required=False, type=str),
        OpenApiParameter(name="consensus_sequence_name", description="", required=False, type=str),
        OpenApiParameter(name="consensus_sequence_software_name", description="", required=False, type=str),
        OpenApiParameter(name="consensus_sequence_software_version", description="", required=False, type=str),
        OpenApiParameter(name="dehosting_method_software_name", description="", required=False, type=str),
        OpenApiParameter(name="dehosting_method_software_version", description="", required=False, type=str),
        OpenApiParameter(name="depth_of_coverage_threshold", description="", required=False, type=str),
        OpenApiParameter(name="depth_of_coverage_value", description="", required=False, type=str),
        OpenApiParameter(name="if_assembly_other", description="", required=False, type=str),
        OpenApiParameter(name="if_bioinformatic_protocol_is_other_specify", description="", required=False, type=str),
        OpenApiParameter(name="if_consensus_other", description="", required=False, type=str),
        OpenApiParameter(name="if_lineage_identification_other", description="", required=False, type=str),
        OpenApiParameter(name="if_mapping_other", description="", required=False, type=str),
        OpenApiParameter(name="if_preprocessing_other", description="", required=False, type=str),
        OpenApiParameter(name="lineage_algorithm_software_version", description="", required=False, type=str),
        OpenApiParameter(name="lineage_analysis_constellation_version", description="", required=False, type=str),
        OpenApiParameter(name="lineage_analysis_date", description="", required=False, type=str),
        OpenApiParameter(name="lineage_analysis_scorpio_version", description="", required=False, type=str),
        OpenApiParameter(name="lineage_analysis_software_name", description="", required=False, type=str),
        OpenApiParameter(name="lineage_analysis_software_version", description="", required=False, type=str),
        OpenApiParameter(name="lineage_name", description="", required=False, type=str),
        OpenApiParameter(name="long_table_path", description="", required=False, type=str),
        OpenApiParameter(name="mapping_params", description="", required=False, type=str),
        OpenApiParameter(name="mapping_software_name", description="", required=False, type=str),
        OpenApiParameter(name="mapping_software_version", description="", required=False, type=str),
        OpenApiParameter(name="ns_per_100_kbp", description="", required=False, type=str),
        OpenApiParameter(name="number_of_base_pairs_sequenced", description="", required=False, type=str),
        OpenApiParameter(name="number_of_variants_in_consensus", description="", required=False, type=str),
        OpenApiParameter(name="number_of_variants_with_effect", description="", required=False, type=str),
        OpenApiParameter(name="per_Ns", description="", required=False, type=str),
        OpenApiParameter(name="per_genome_greater_10x", description="", required=False, type=str),
        OpenApiParameter(name="per_reads_host", description="", required=False, type=str),
        OpenApiParameter(name="per_reads_virus", description="", required=False, type=str),
        OpenApiParameter(name="per_unmapped", description="", required=False, type=str),
        OpenApiParameter(name="preprocessing_params", description="", required=False, type=str),
        OpenApiParameter(name="preprocessing_software_name", description="", required=False, type=str),
        OpenApiParameter(name="preprocessing_software_version", description="", required=False, type=str),
        OpenApiParameter(name="qc_filtered", description="", required=False, type=str),
        OpenApiParameter(name="reference_genome_accession", description="", required=False, type=str),
        OpenApiParameter(name="schema_name", description="Name of the Schema. (Relecov)", required=True, type=str),
        OpenApiParameter(name="schema_version", description="Version of the Schema. ", required=True, type=str),
        OpenApiParameter(name="sequence_file_R1_fastq", description="", required=False, type=str),
        OpenApiParameter(name="sequence_file_R1_md5", description="", required=False, type=str),
        OpenApiParameter(name="sequence_file_R2_fastq", description="", required=False, type=str),
        OpenApiParameter(name="sequence_file_R2_md5", description="", required=False, type=str),
        OpenApiParameter(name="sequencing_sample_id", description="", required=True, type=str),
        OpenApiParameter(name="variant_calling_params", description="", required=False, type=str),
        OpenApiParameter(name="variant_calling_software_name", description="", required=False, type=str),
        OpenApiParameter(name="variant_calling_software_version", description="", required=False, type=str),
        OpenApiParameter(name="variant_name", description="", required=False, type=str),
    ],
    description='More descriptive text',
    responses={
        201: OpenApiResponse(description="Successful upload information"),
        400: OpenApiResponse(description="Bad request"),
        500: OpenApiResponse(description="Internal Server Error"),
    },
)
"""


@extend_schema(
    examples=[
        OpenApiExample(
            "Example",
            description="Variant example",
            value={
                "analysis_date": "20220705",
                "assembly": "None",
                "assembly_params": "None",
                "bioinformatics_protocol_software_name": "nf-core/viralrecon",
                "bioinformatics_protocol_software_version": "2.4.1",
                "commercial_open_source_both": "Open Source",
                "consensus_genome_length": "29884",
                "consensus_params": "-p vcf -f",
                "consensus_sequence_filename": "2018086.consensus.fa",
                "consensus_sequence_filepath": "/data/COD-2100/20220720",
                "consensus_sequence_md5": "8853df0702f68d4e50bb3aab59a59df9",
                "consensus_sequence_name": "21578522",
                "consensus_sequence_software_name": "BCFTOOLS_CONSENSUS",
                "consensus_sequence_software_version": "1.14",
                "dehosting_method_software_name": "KRAKEN2_KRAKEN2",
                "dehosting_method_software_version": "2.1.2",
                "depth_of_coverage_threshold": ">10x",
                "depth_of_coverage_value": "1804.46",
                "if_consensus_other": "None",
                "if_enrichment_panel_assay_is_other_specify": "Not Provided",
                "if_enrichment_protocol_is_other_specify": "Not Provided",
                "if_lineage_identification_other": "None",
                "if_mapping_other": "None",
                "if_preprocessing_other": "None",
                "lineage_algorithm_software_version": "PUSHER-v1.9",
                "lineage_analysis_constellation_version": "v0.1.10",
                "lineage_analysis_date": "2022-07-05",
                "lineage_analysis_scorpio_version": "0.3.17",
                "lineage_analysis_software_name": "pangolin",
                "lineage_analysis_software_version": "4.0.6",
                "lineage_name": "B.1.1.7",
                "long_table_path": "",
                "mapping_params": "--seed 1",
                "mapping_software_name": "BOWTIE2_ALIGN",
                "mapping_software_version": "2.4.4",
                "number_of_base_pairs_sequenced": "9024968",
                "number_of_samples_in_run": "60",
                "number_of_variants_in_consensus": "34",
                "number_of_variants_with_effect": "22",
                "per_Ns": "1.63",
                "per_genome_greater_10x": "99.66",
                "per_reads_host": "0.23",
                "per_reads_virus": "99.7446",
                "per_unmapped": "0.0223003",
                "preprocessing_params": "--cut_front --cut_tail --trim_poly_x --cut_mean_quality 30 --qualified_quality_phred 30 --unqualified_percent_limit 10 --length_required 50",
                "preprocessing_software_name": "FASTP",
                "preprocessing_software_version": "0.23.2",
                "qc_filtered": "573984",
                "reference_genome_accession": "NC_045512.2",
                "schema_name": "RELECOV schema",
                "schema_version": "1.0.0",
                "sequence_file_R1_fastq": "2018086_R1.fastq.gz",
                "sequence_file_R1_md5": "eab8b05ef27f4f5cba5cddf6ad627de2",
                "sequence_file_R2_fastq": "2018086_R2.fastq.gz",
                "sequence_file_R2_md5": "d82a37aa970df2b8bf8f547ca7c18ac8",
                "sequencing_sample_id": "254866",
                "variant_calling_params": "--ignore-overlaps --count-orphans --no-BAQ --max-depth 0 --min-BQ 0';-t 0.25 -q 20 -m 10",
                "variant_calling_software_name": "IVAR_VARIANTS",
                "variant_calling_software_version": "1.3.1",
                "variant_name": "Alpha (B.1.1.7-like)",
            },
        )
    ],
    request=inline_serializer(
        name="create_bioinfo_metadata",
        fields={
            "analysis_date": serializers.CharField(),
            "assembly": serializers.CharField(),
            "assembly_params": serializers.CharField(),
            "bioinformatics_protocol_software_name": serializers.CharField(),
            "bioinformatics_protocol_software_version": serializers.CharField(),
            "commercial_open_source_both": serializers.CharField(),
            "consensus_genome_length": serializers.CharField(),
            "consensus_params": serializers.CharField(),
            "consensus_sequence_filename": serializers.CharField(),
            "consensus_sequence_filepath": serializers.CharField(),
            "consensus_sequence_md5": serializers.CharField(),
            "consensus_sequence_name": serializers.CharField(),
            "consensus_sequence_software_name": serializers.CharField(),
            "consensus_sequence_software_version": serializers.CharField(),
            "dehosting_method_software_name": serializers.CharField(),
            "dehosting_method_software_version": serializers.CharField(),
            "depth_of_coverage_threshold": serializers.CharField(),
            "depth_of_coverage_value": serializers.CharField(),
            "if_assembly_other": serializers.CharField(),
            "if_bioinformatic_protocol_is_other_specify": serializers.CharField(),
            "if_consensus_other": serializers.CharField(),
            "if_lineage_identification_other": serializers.CharField(),
            "if_mapping_other": serializers.CharField(),
            "if_preprocessing_other": serializers.CharField(),
            "lineage_algorithm_software_version": serializers.CharField(),
            "lineage_analysis_constellation_version": serializers.CharField(),
            "lineage_analysis_date": serializers.CharField(),
            "lineage_analysis_scorpio_version": serializers.CharField(),
            "lineage_analysis_software_name": serializers.CharField(),
            "lineage_analysis_software_version": serializers.CharField(),
            "lineage_name": serializers.CharField(),
            "long_table_path": serializers.CharField(),
            "mapping_params": serializers.CharField(),
            "mapping_software_name": serializers.CharField(),
            "mapping_software_version": serializers.CharField(),
            "ns_per_100_kbp": serializers.CharField(),
            "number_of_base_pairs_sequenced": serializers.CharField(),
            "number_of_variants_in_consensus": serializers.CharField(),
            "number_of_variants_with_effect": serializers.CharField(),
            "per_Ns": serializers.CharField(),
            "per_genome_greater_10x": serializers.CharField(),
            "per_reads_host": serializers.CharField(),
            "per_reads_virus": serializers.CharField(),
            "per_unmapped": serializers.CharField(),
            "preprocessing_params": serializers.CharField(),
            "preprocessing_software_name": serializers.CharField(),
            "preprocessing_software_version": serializers.CharField(),
            "qc_filtered": serializers.CharField(),
            "reference_genome_accession": serializers.CharField(),
            "schema_name": serializers.CharField(),
            "schema_version": serializers.CharField(),
            "sequence_file_R1_fastq": serializers.CharField(),
            "sequence_file_R1_md5": serializers.CharField(),
            "sequence_file_R2_fastq": serializers.CharField(),
            "sequence_file_R2_md5": serializers.CharField(),
            "sequencing_sample_id": serializers.CharField(),
            "variant_calling_params": serializers.CharField(),
            "variant_calling_software_name": serializers.CharField(),
            "variant_calling_software_version": serializers.CharField(),
            "variant_name": serializers.CharField(),
        },
    ),
    description="More descriptive text",
    responses={
        201: OpenApiResponse(description="Successful C information"),
        400: OpenApiResponse(description="Bad request"),
        500: OpenApiResponse(description="Internal Server Error"),
    },
)
@authentication_classes([SessionAuthentication, BasicAuthentication])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_bioinfo_metadata(request):
    if request.method == "POST":
        data = request.data

    if isinstance(data, QueryDict):
        data = data.dict()
    # check schema (name and version)
    schema_obj = get_schema_version_if_exists(data)
    if schema_obj is None:
        error = {"ERROR": "schema name and version is not defined"}
        return Response(error, status=status.HTTP_400_BAD_REQUEST)
    if "sequencing_sample_id" not in data:
        return Response(
            {"ERROR": ERROR_SAMPLE_NAME_NOT_INCLUDED},
            status=status.HTTP_400_BAD_REQUEST,
        )
    sample_obj = get_sample_obj_from_sample_name(data["sequencing_sample_id"])
    if sample_obj is None:
        return Response(
            {"ERROR": ERROR_SAMPLE_NOT_DEFINED}, status=status.HTTP_400_BAD_REQUEST
        )

    analysis_defined = get_analysis_defined(sample_obj)
    if data["analysis_date"] in list(analysis_defined):
        return Response(
            {"ERROR": ERROR_ANALYSIS_ALREADY_DEFINED},
            status=status.HTTP_400_BAD_REQUEST,
        )
    split_data = split_bioinfo_data(data, schema_obj)
    if "ERROR" in split_data:
        return Response(split_data, status=status.HTTP_400_BAD_REQUEST)

    stored_data = store_bioinfo_data(split_data, schema_obj)
    if "ERROR" in stored_data:
        return Response(stored_data, status=status.HTTP_400_BAD_REQUEST)
    state_id = SampleState.objects.filter(state__exact="Bioinfo").last().get_state_id()
    data_date = {"sampleID": sample_obj.get_sample_id(), "stateID": state_id}

    # update sample state
    sample_obj.update_state("Bioinfo")
    # Include date and state in DateState table
    date_serializer = CreateDateAfterChangeStateSerializer(data=data_date)
    if date_serializer.is_valid():
        date_serializer.save()

    return Response(status=status.HTTP_201_CREATED)


@extend_schema(
    examples=[
        OpenApiExample(
            "Example",
            description="Variant example",
            value={
                "sample_name": "sample_name_12345",
                "variants": [
                    {
                        "Chromosome": "NC_045512.2",
                        "Variant": {"pos": "11287", "alt": "G", "ref": "GTCTGGTTTT"},
                        "Filter": "PASS",
                        "VariantInSample": {
                            "dp": "1322",
                            "ref_dp": "1312",
                            "alt_dp": "1197",
                            "af": "0.91",
                        },
                        "Gene": "orf1ab",
                        "Effect": "conservative_inframe_deletion",
                        "VariantAnnotation": {
                            "hgvs_c": "c.11023_11031delTCTGGTTTT",
                            "hgvs_p": "p.Ser3675_Phe3677del",
                            "hgvs_p_1_letter": "p.S3675_F3677del",
                        },
                    },
                    {
                        "Chromosome": "NC_045512.2",
                        "Variant": {"pos": "13386", "alt": "A", "ref": "G"},
                        "Filter": "PASS",
                        "VariantInSample": {
                            "dp": "14750",
                            "ref_dp": "8029",
                            "alt_dp": "6307",
                            "af": "0.43",
                        },
                        "Gene": "orf1ab",
                        "Effect": "missense_variant",
                        "VariantAnnotation": {
                            "hgvs_c": "c.13121G>A",
                            "hgvs_p": "p.Gly4374Asp",
                            "hgvs_p_1_letter": "p.G4374D",
                        },
                    },
                ],
            },
        )
    ],
    description="Store variants found for the sample",
    responses={
        201: OpenApiResponse(description="Successful upload information"),
        400: OpenApiResponse(description="Bad request"),
        500: OpenApiResponse(description="Internal Server Error"),
    },
    request=inline_serializer(
        name="VariantUpload",
        fields={
            "sample_name": serializers.CharField(),
            "Variants": serializers.ListField(
                child=serializers.DictField(
                    child=serializers.CharField(label="ere"), label="Chromosome"
                )
            ),
            "Chromosome": serializers.CharField(),
            "variant": serializers.DictField(child=serializers.CharField()),
            "pos": serializers.CharField(),
            "alt": serializers.CharField(),
            "ref": serializers.DictField(child=serializers.CharField(), label="po"),
            "file_field": serializers.FileField(),
            "pepe": serializers.JSONField(),
        },
    ),
)
@authentication_classes([SessionAuthentication, BasicAuthentication])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_variant_data(request):
    if request.method == "POST":
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()

        sample_obj = get_sample_obj_from_sample_name(data["sample_name"])
        if sample_obj is None:
            return Response(
                {"ERROR": ERROR_SAMPLE_NOT_DEFINED}, status=status.HTTP_400_BAD_REQUEST
            )
        analysis_defined = get_variant_analysis_defined(sample_obj)
        if data["analysis_date"] in list(analysis_defined):
            return Response(
                {"ERROR": ERROR_ANALYSIS_ALREADY_DEFINED},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "variants" not in data:
            return Response(
                {"ERROR": ERROR_VARIANT_INFORMATION_NOT_DEFINED},
                status=status.HTTP_400_BAD_REQUEST,
            )
        found_error = False
        v_in_sample_list = []
        v_an_list = []

        for v_data in data["variants"]:
            split_data = split_variant_data(v_data, sample_obj, data["analysis_date"])
            if "ERROR" in split_data:
                error = {"ERROR": split_data}
                found_error = True
                break

            variant_in_sample_obj = store_variant_in_sample(
                split_data["variant_in_sample"]
            )
            if isinstance(variant_in_sample_obj, dict):
                error = {"ERROR": variant_in_sample_obj}
                found_error = True
                break

            v_in_sample_list.append(variant_in_sample_obj)

            if not variant_annotation_exists(split_data["variant_ann"]):
                variant_ann_obj = store_variant_annotation(split_data["variant_ann"])
                if isinstance(variant_ann_obj, dict):
                    error = {"ERROR": variant_ann_obj}
                    found_error = True
                    break

                v_an_list.append(variant_ann_obj)

        if found_error:
            delete_created_variancs(v_in_sample_list, v_an_list)
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        sample_obj.update_state("Variant")
        # Include date and state in DateState table
        state_id = (
            SampleState.objects.filter(state__exact="Variant").last().get_state_id()
        )
        sample_id = sample_obj.get_sample_id()
        update_change_state_date(sample_id, state_id)

        return Response(status=status.HTTP_201_CREATED)
    return Response(error, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    examples=[
        OpenApiExample(
            name="update sample state",
            value={"sample_name": "sample_number_12345", "state": "Bioinfo"},
        )
    ],
    request=inline_serializer(
        name="UpdateState",
        fields={
            "sample_name": serializers.CharField(),
            "state": serializers.CharField(),
        },
    ),
    responses={
        201: OpenApiResponse(description="Successful. sample state updated"),
        400: OpenApiResponse(description="Bad Request"),
        500: OpenApiResponse(description="Internal Server Error"),
    },
)
@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@api_view(["PUT"])
def update_state(request):
    if request.method == "PUT":
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()
        data["user"] = request.user.pk
        sample_obj = get_sample_obj_from_sample_name(data["sample_name"])
        if sample_obj is None:
            return Response(
                {"ERROR": ERROR_SAMPLE_NOT_DEFINED}, status=status.HTTP_400_BAD_REQUEST
            )
        sample_id = sample_obj.get_sample_id()
        # if state exists,
        if SampleState.objects.filter(state=data["state"]).exists():
            s_data = {
                "state": SampleState.objects.filter(state=data["state"])
                .last()
                .get_state_id()
            }
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        sample_serializer = UpdateStateSampleSerializer(sample_obj, data=s_data)
        if not sample_serializer.is_valid():
            return Response(
                sample_serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )
        sample_serializer.save()

        if "error_type" in data and "Error" in data["state"]:
            error_type_id = (
                Error.objects.filter(error_name=data["error_type"])
                .last()
                .get_error_id()
            )
            e_data = {"error_type": error_type_id}
            sample_err_serializer = CreateErrorSerializer(sample_obj, data=e_data)
            if not sample_err_serializer.is_valid():
                return Response(
                    sample_err_serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )
            sample_err_serializer.save()

        update_change_state_date(sample_id, s_data["state"])

        return Response(
            "Successful. sample state updated", status=status.HTTP_201_CREATED
        )
    return Response(status=status.HTTP_400_BAD_REQUEST)
