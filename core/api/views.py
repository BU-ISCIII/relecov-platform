# Generic imports
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
    api_view,
)
from rest_framework import status
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    inline_serializer,
    OpenApiResponse,
)
from rest_framework import serializers
from django.http import QueryDict
import ast
from django.db import transaction

# Local imports
import core.urls
import core.models
import core.utils.samples
import core.api.serializers
import core.api.utils.samples
import core.api.utils.bioinfo_metadata
import core.api.utils.public_db
import core.api.utils.variants
import core.api.utils.common_functions
import core.config
import core.utils.lab_catalog


@extend_schema(
    examples=[
        OpenApiExample(
            "Example",
            description="Variant example",
            value={
                "analysis_authors": "",
                "author_submitter": "",
                "authors": "",
                "experiment_alias": "",
                "experiment_title": "",
                "sequence_file_R1_md5": "b5242d60471e5a5a97b35531dbbe8c30",
                "sequence_file_R2_md5": "57525c5a1ec992098e652aa01b366d69",
                "gisaid_id": "EPI_ISL_8625444",
                "microbiology_lab_sample_id": "20183102",
                "sequence_file_path_R1": "/media/data/relecov/",
                "sequence_file_path_R2": "/media/data/relecov/",
                "schema_name": "relecov",
                "schema_version": "",
                "sequence_file_R1": "20183102_R1.fastq.gz",
                "sequence_file_R2": "20183102_R2.fastq.gz",
                "sequencing_sample_id": "20183102",
                "study_alias": "",
                "study_id": "",
                "study_title": "",
                "study_type": "Whole Genome Sequencing",
                "submitting_lab_sample_id": "LAB_856232",
                "collecting_institution_code_1": "1328000027",
            },
        )
    ],
    request=inline_serializer(
        name="createSample",
        fields={
            "analysis_authors": serializers.CharField(required=False),
            "author_submitter": serializers.CharField(required=False),
            "authors": serializers.CharField(required=False),
            "experiment_alias": serializers.CharField(required=False),
            "experiment_title": serializers.CharField(required=False),
            "sequence_file_R1_md5": serializers.CharField(),
            "sequence_file_R2_md5": serializers.CharField(),
            "gisaid_id": serializers.CharField(required=False),
            "microbiology_lab_sample_id": serializers.CharField(),
            "sequence_file_path_R1": serializers.CharField(),
            "sequence_file_path_R2": serializers.CharField(),
            "schema_name": serializers.CharField(),
            "schema_version": serializers.CharField(),
            "sequence_file_R1": serializers.CharField(),
            "sequence_file_R2": serializers.CharField(),
            "sequencing_sample_id": serializers.CharField(),
            "study_alias": serializers.CharField(required=False),
            "study_id": serializers.CharField(required=False),
            "study_title": serializers.CharField(required=False),
            "study_type": serializers.CharField(required=False),
            "submitting_lab_sample_id": serializers.CharField(),
            "collecting_institution_code_1": serializers.CharField(),
        },
    ),
    description="More descriptive text",
    responses={
        201: OpenApiResponse(
            description="The created Sample object",
            response=core.api.serializers.CreateSampleSerializer,
            examples=[
                OpenApiExample(
                    "SuccessExample",
                    value={
                        "message": "Successful upload information",
                        "data": {
                            "id": 756879,
                            "sample_unique_id": "ABE-3704",
                            "sequencing_sample_id": "20183102",
                            "microbiology_lab_sample_id": "None",
                            "collecting_lab_sample_id": "1000",
                            "submitting_lab_sample_id": "None",
                            "collecting_institution": "Instituto de Salud Carlos III",
                            "lab_code_1": "1328000027",
                            "submitting_institution": "Instituto de Salud Carlos III",
                            "sequence_file_R1": "SAMPLE1_R1.fastq.gz",
                            "sequence_file_R2": "SAMPLE1_R2.fastq.gz",
                            "sequence_file_R1_md5": "c7e94849f9a8b0c15eb1cc720295ee80",
                            "sequence_file_R2_md5": "04c5bfb372dc7c5f181a5fbd53c1a1f2",
                            "sequence_file_path_R1": "tests/data/datatest1/",
                            "sequence_file_path_R2": "tests/data/datatest1/",
                            "sequencing_date": "2023-03-23T00:00:00",
                            "sample_fingerprint": "e7b6061c668e4c5034fffc3f",
                            "created_at": "2023-02-21T13:43:32.772926",
                            "state": "1",
                            "user": "None",
                            "error_type": "None",
                            "schema_obj": "4",
                            "lineage_values": "[]",
                            "lineage_info": "[]",
                            "bio_analysis_values": "[]",
                        },
                    },
                )
            ],
        ),
        409: OpenApiResponse(
            response=core.api.serializers.CreateSampleSerializer,
            examples=[
                OpenApiExample(
                    "SampleAlreadyDefinedExample",
                    value={
                        "ERROR": "Sample already defined.",
                        "data": {
                            "id": 756879,
                            "sample_unique_id": "ABE-3704",
                            "sequencing_sample_id": "20183102",
                            "microbiology_lab_sample_id": "None",
                            "collecting_lab_sample_id": "1000",
                            "submitting_lab_sample_id": "None",
                            "collecting_institution": "Instituto de Salud Carlos III",
                            "lab_code_1": "1328000027",
                            "submitting_institution": "Instituto de Salud Carlos III",
                            "sequence_file_R1": "SAMPLE1_R1.fastq.gz",
                            "sequence_file_R2": "SAMPLE1_R2.fastq.gz",
                            "sequence_file_R1_md5": "c7e94849f9a8b0c15eb1cc720295ee80",
                            "sequence_file_R2_md5": "04c5bfb372dc7c5f181a5fbd53c1a1f2",
                            "sequence_file_path_R1": "tests/data/datatest1/",
                            "sequence_file_path_R2": "tests/data/datatest1/",
                            "sequencing_date": "2023-03-23T00:00:00",
                            "sample_fingerprint": "e7b6061c668e4c5034fffc3f",
                            "created_at": "2023-02-21T13:43:32.772926",
                            "state": "1",
                            "user": "None",
                            "error_type": "None",
                            "schema_obj": "4",
                            "lineage_values": "[]",
                            "lineage_info": "[]",
                            "bio_analysis_values": "[]",
                        },
                    },
                )
            ],
        ),
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

        schema_obj = core.api.utils.common_functions.get_schema_version_if_exists(data)
        if schema_obj is None:
            error = {
                "ERROR": "schema name and version is not defined",
                "message": "",
                "data": {},
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        schema_id = schema_obj.get_schema_id()
        # Check mandatory identifiers (lab name is derived further below if needed)
        required_db_fields = [
            "sequencing_sample_id",
            "collecting_lab_sample_id",
            "submitting_institution",
        ]
        missing_fields = [f for f in required_db_fields if not data.get(f)]
        if missing_fields:
            print(f"ERROR. Missing: {missing_fields}")
            return Response(
                {"ERROR": f"Missing: {missing_fields}", "message": "", "data": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        lab_code_field = "collecting_institution_code_1"
        lab_code_raw = data.get(lab_code_field)
        lab_code_value = str(lab_code_raw).strip() if lab_code_raw else ""
        if lab_code_value in core.config.FIELD_EMPTY_VALUES or not lab_code_value:
            print(f"ERROR. Missing: [{lab_code_field}]")
            return Response(
                {
                    "ERROR": f"Missing: [{lab_code_field}]",
                    "message": "",
                    "data": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        resolved_collecting_name = core.utils.lab_catalog.ensure_lab_display(
            lab_code_value, fallback_name=data.get("collecting_institution")
        )
        provided_collecting_name = data.get("collecting_institution", "").strip()
        canonical_collecting_name = resolved_collecting_name or provided_collecting_name
        if not canonical_collecting_name:
            print("Unable to resolve collecting_institution from lab_code_1")
            return Response(
                {
                    "ERROR": "Missing: ['collecting_institution']. Could not resolve from lab_code_1",
                    "message": "",
                    "data": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        data["collecting_institution"] = canonical_collecting_name
        # Include collecting_institution in the required fields list for fingerprint
        required_db_fields.append("collecting_institution")
        # check if sample is already defined
        temp_fingerprint = core.utils.samples.build_sample_fingerprint(
            *[data[field] for field in required_db_fields]
        )
        found_sample = core.utils.samples.get_sample_obj_from_fingerprint(
            temp_fingerprint
        )
        if found_sample:
            found_data = core.api.serializers.CreateSampleSerializer(found_sample).data
            error = {
                "ERROR": "Sample already defined.",
                "message": "",
                "data": found_data,
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        # get the user to assign the sample based on the collecting_institution
        # value. If lab is not define user field is set t
        split_data = core.api.utils.samples.split_sample_data(data)
        # Add schema id to store in database
        split_data["sample"]["schema_obj"] = schema_id
        split_data["sample"]["lab_code_1"] = lab_code_value
        split_data["sample"]["collecting_institution"] = data["collecting_institution"]
        sample_serializer = core.api.serializers.CreateSampleSerializer(
            data=split_data["sample"]
        )
        if not sample_serializer.is_valid():
            return Response(
                {"ERROR": sample_serializer.errors, "message": "", "data": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sample_obj = sample_serializer.save()
        sample_id = sample_obj.get_sample_id()
        # update sample state date
        data = {
            "sampleID": sample_id,
            "stateID": split_data["sample"]["state"],
        }
        date_serilizer = core.api.serializers.CreateDateAfterChangeStateSerializer(
            data=data
        )
        if date_serilizer.is_valid():
            date_serilizer.save()

        # Save ENA info if included
        if split_data.get("ena") and any(split_data["ena"].values()):
            result = core.api.utils.public_db.store_pub_databases_data(
                split_data["ena"], "ena", schema_obj, sample_id
            )
            if "ERROR" in result:
                response_dict = {
                    "ERROR": result["ERROR"],
                    "message": "Error processing ena data",
                    "data": {},
                }
                return Response(response_dict, status=status.HTTP_206_PARTIAL_CONTENT)
            # check that the ena_sample_accession is not empty or "Not Provided"
            if not any(
                x == split_data["ena"]["ena_sample_accession"]
                for x in core.config.FIELD_EMPTY_VALUES
            ):
                # Save entry in update state table for valid ena_sample_accession
                sample_obj.update_state("Ena")
                state_id = (
                    core.models.SampleState.objects.filter(state__exact="Ena")
                    .last()
                    .get_state_id()
                )
                data = {"sampleID": sample_id, "stateID": state_id}
                date_serilizer = (
                    core.api.serializers.CreateDateAfterChangeStateSerializer(data=data)
                )
                if date_serilizer.is_valid():
                    date_serilizer.save()
        # Save GISAID info if included
        if split_data.get("gisaid") and any(split_data["gisaid"].values()):
            for key in ["gisaid_accession_id", "gisaid_virus_name"]:
                if not split_data["gisaid"].get(key):
                    split_data["gisaid"][key] = "Not Provided"

            result = core.api.utils.public_db.store_pub_databases_data(
                split_data["gisaid"], "gisaid", schema_obj, sample_id
            )
            if "ERROR" in result:
                response_dict = {
                    "ERROR": result,
                    "message": "Error processing gisaid data",
                    "data": {},
                }
                return Response(response_dict, status=status.HTTP_400_BAD_REQUEST)

            # Save entry in update state table only if gisaid_accession_id is valid
            gisaid_id = split_data["gisaid"].get("gisaid_accession_id")
            if gisaid_id and isinstance(gisaid_id, str) and "EPI_ISL" in gisaid_id:
                sample_obj.update_state("Gisaid")
                state_id = (
                    core.models.SampleState.objects.filter(state__exact="Gisaid")
                    .last()
                    .get_state_id()
                )
                data = {"sampleID": sample_id, "stateID": state_id}
                date_serilizer = (
                    core.api.serializers.CreateDateAfterChangeStateSerializer(data=data)
                )
                if date_serilizer.is_valid():
                    date_serilizer.save()

        # Save AUTHOR info if included
        if len(split_data["author"]) > 0:
            result = core.api.utils.public_db.store_pub_databases_data(
                split_data["author"], "author", schema_obj, sample_id
            )
            if "ERROR" in result:
                response_dict = {
                    "ERROR": result,
                    "message": "Error processing authors data",
                    "data": {},
                }
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
        sample_dict = core.api.serializers.CreateSampleSerializer(sample_obj).data
        return Response(
            {"message": "Successful upload information", "data": sample_dict},
            status=status.HTTP_201_CREATED,
        )


@extend_schema(
    examples=[
        OpenApiExample(
            "Example",
            description="Variant example",
            value={
                "bioinformatics_analysis_date": "20220705",
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
                "lineage_assignment_constellation_version": "v0.1.10",
                "lineage_assignment_date": "2022-07-05",
                "lineage_assignment_scorpio_version": "0.3.17",
                "lineage_assignment_software_name": "pangolin",
                "lineage_assignment_software_version": "4.0.6",
                "lineage_name": "B.1.1.7",
                "long_table_path": "",
                "mapping_params": "--seed 1",
                "mapping_software_name": "BOWTIE2_ALIGN",
                "mapping_software_version": "2.4.4",
                "number_of_reads_sequenced": "9024968",
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
                "pass_reads": "573984",
                "reference_genome_accession": "NC_045512.2",
                "schema_name": "RELECOV schema",
                "schema_version": "1.0.0",
                "sequence_file_R1": "2018086_R1.fastq.gz",
                "sequence_file_R1_md5": "eab8b05ef27f4f5cba5cddf6ad627de2",
                "sequence_file_R2": "2018086_R2.fastq.gz",
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
            "unique_sample_id": serializers.CharField(),
            "bioinformatics_analysis_date": serializers.CharField(),
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
            "if_assembly_other": serializers.CharField(required=False),
            "if_bioinformatic_protocol_is_other_specify": serializers.CharField(
                required=False
            ),
            "if_consensus_other": serializers.CharField(required=False),
            "if_lineage_identification_other": serializers.CharField(required=False),
            "if_mapping_other": serializers.CharField(required=False),
            "if_preprocessing_other": serializers.CharField(required=False),
            "lineage_algorithm_software_version": serializers.CharField(),
            "lineage_assignment_constellation_version": serializers.CharField(),
            "lineage_assignment_date": serializers.CharField(),
            "lineage_assignment_scorpio_version": serializers.CharField(),
            "lineage_assignment_software_name": serializers.CharField(),
            "lineage_assignment_software_version": serializers.CharField(),
            "lineage_name": serializers.CharField(),
            "long_table_path": serializers.CharField(),
            "mapping_params": serializers.CharField(),
            "mapping_software_name": serializers.CharField(),
            "mapping_software_version": serializers.CharField(),
            "ns_per_100_kbp": serializers.CharField(),
            "number_of_reads_sequenced": serializers.CharField(),
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
            "pass_reads": serializers.CharField(),
            "reference_genome_accession": serializers.CharField(),
            "schema_name": serializers.CharField(),
            "schema_version": serializers.CharField(),
            "sequence_file_R1": serializers.CharField(),
            "sequence_file_R1_md5": serializers.CharField(),
            "sequence_file_R2": serializers.CharField(),
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
    schema_obj = core.api.utils.common_functions.get_schema_version_if_exists(data)
    if schema_obj is None:
        error = {
            "ERROR": "schema name and version is not defined",
            "message": "Error found while extracting schema object",
            "data": {},
        }
        return Response(error, status=status.HTTP_400_BAD_REQUEST)
    if "unique_sample_id" not in data:
        error = {
            "ERROR": core.config.ERROR_SAMPLE_NAME_NOT_INCLUDED,
            "message": "Error no unique sample id in data",
            "data": {},
        }
        return Response(error, status=status.HTTP_400_BAD_REQUEST)
    sample_obj = core.utils.samples.get_sample_obj_from_unique_sample_id(
        data["unique_sample_id"]
    )
    if sample_obj is None:
        error = {
            "ERROR": core.config.ERROR_SAMPLE_NOT_DEFINED,
            "message": "Error searching for requested sample",
            "data": {},
        }
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    analysis_defined = core.api.utils.bioinfo_metadata.get_analysis_defined(sample_obj)
    bioinformatics_analysis_date = data.get("bioinformatics_analysis_date", None)
    if bioinformatics_analysis_date is not None:
        if bioinformatics_analysis_date in list(analysis_defined):
            error = {
                "ERROR": core.config.ERROR_ANALYSIS_ALREADY_DEFINED,
                "message": "Found another sample analysis with the same date",
                "data": {},
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

    split_data = core.api.utils.bioinfo_metadata.split_bioinfo_data(data, schema_obj)
    if "ERROR" in split_data:
        error = {
            "ERROR": split_data["ERROR"],
            "message": "error extracting bioinfo metadata",
            "data": {},
        }
        return Response(error, status=status.HTTP_400_BAD_REQUEST)

    stored_data = core.api.utils.bioinfo_metadata.store_bioinfo_data(
        split_data, schema_obj
    )
    if "ERROR" in stored_data:
        error = {
            "ERROR": stored_data["ERROR"],
            "message": "error storing bioinfo metadata",
            "data": {},
        }
        return Response(error, status=status.HTTP_400_BAD_REQUEST)
    state_id = (
        core.models.SampleState.objects.filter(state__exact="Bioinfo")
        .last()
        .get_state_id()
    )
    data_date = {"sampleID": sample_obj.get_sample_id(), "stateID": state_id}

    # update sample state
    sample_obj.update_state("Bioinfo")
    # Include date and state in DateState table
    date_serializer = core.api.serializers.CreateDateAfterChangeStateSerializer(
        data=data_date
    )
    if date_serializer.is_valid():
        date_serializer.save()

    return Response(
        {
            "message": f"Bioinfo metadata successfully saved for sample {sample_obj.get_sequencing_sample_id()}",
            "data": {
                "sample_unique_id": getattr(sample_obj, "sample_unique_id", None)
                or sample_obj.get_sample_unique_id(),
                "sample_id": sample_obj.get_sample_id(),
                "sequencing_sample_id": sample_obj.get_sequencing_sample_id(),
                "bioinformatics_analysis_date": bioinformatics_analysis_date,
                "state": "Bioinfo",
            },
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    examples=[
        OpenApiExample(
            "Example",
            description="Variant example",
            value={
                "sample_name": "sample_name_12345",
                "unique_sample_id": "RLCV-0000001234",
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
            "unique_sample_id": serializers.CharField(required=False),
            "Variants": inline_serializer(
                name="variant",
                fields={
                    "Chromosome": serializers.CharField(),
                    "variant": inline_serializer(
                        name="variant",
                        fields={
                            "pos": serializers.CharField(),
                            "alt": serializers.CharField(),
                            "ref": serializers.CharField(),
                        },
                    ),
                    "Filter": serializers.CharField(),
                    "VariantInSample": inline_serializer(
                        name="VariantInSample",
                        fields={
                            "dp": serializers.CharField(),
                            "ref_dp": serializers.CharField(),
                            "alt_dp": serializers.CharField(),
                            "af": serializers.CharField(),
                        },
                    ),
                    "Gene": serializers.CharField(),
                    "Effect": serializers.CharField(),
                    "VariantAnnotation": inline_serializer(
                        name="VariantAnnotation",
                        fields={
                            "hgvs_c": serializers.CharField(),
                            "hgvs_p": serializers.CharField(),
                            "hgvs_p_1_letter": serializers.CharField(),
                        },
                        allow_null=True,
                    ),
                },
            ),
        },
    ),
)
@authentication_classes([SessionAuthentication, BasicAuthentication])
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_variant_data(request):
    CHUNK_SIZE = 250

    if request.method == "POST":
        data = request.data
        if isinstance(data, QueryDict):
            data = data.dict()

        sample_name = data.get("sample_name")
        unique_sample_id = data.get("unique_sample_id")
        sample_obj = None

        # 1) Prioritise explicit unique_sample_id
        if unique_sample_id:
            sample_obj = core.utils.samples.get_sample_obj_from_unique_sample_id(
                unique_sample_id
            )
            if sample_obj is None:
                error = {
                    "ERROR": core.config.ERROR_SAMPLE_NOT_DEFINED,
                    "message": f"Sample not found for unique_sample_id '{unique_sample_id}'",
                    "data": {},
                }
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

        # 2) Fallback to any provided sample_name
        if sample_obj is None and sample_name:
            sample_obj = core.utils.samples.get_sample_obj_from_sample_name(sample_name)
            if sample_obj is None:
                # sample_name might already contain the unique identifier
                sample_obj = core.utils.samples.get_sample_obj_from_unique_sample_id(
                    sample_name
                )

        if sample_obj is None:
            error = {
                "ERROR": core.config.ERROR_SAMPLE_NOT_DEFINED,
                "message": "Sample identifier not found in platform",
                "data": {},
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        # 3) If both identifiers are provided, ensure they refer to the same sample
        if unique_sample_id and sample_name:
            sample_unique = (getattr(sample_obj, "sample_unique_id", "") or "").strip()
            sample_seq = (getattr(sample_obj, "sequencing_sample_id", "") or "").strip()
            sample_name_norm = sample_name.strip().casefold()
            sample_unique_norm = sample_unique.casefold() if sample_unique else ""
            sample_seq_norm = sample_seq.casefold() if sample_seq else ""
            matches_unique = sample_name_norm == sample_unique_norm
            matches_seq = sample_name_norm == sample_seq_norm
            if not (matches_unique or matches_seq):
                error = {
                    "ERROR": core.config.ERROR_SAMPLE_NOT_DEFINED,
                    "message": (
                        "sample_name does not match the provided unique_sample_id for the same sample"
                    ),
                    "data": {},
                }
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
        analysis_defined = core.api.utils.variants.get_variant_analysis_defined(
            sample_obj
        )
        if data["bioinformatics_analysis_date"] in list(analysis_defined):
            error = {
                "ERROR": core.config.ERROR_ANALYSIS_ALREADY_DEFINED,
                "message": "",
                "data": {},
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        if "variants" not in data:
            error = {
                "ERROR": core.config.ERROR_VARIANT_INFORMATION_NOT_DEFINED,
                "message": "`variants` key could not be found in data",
                "data": {},
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(data["variants"], str):
            try:
                data["variants"] = ast.literal_eval(data["variants"])
            except Exception as e:
                error = {
                    "ERROR": f"Unable to parse variants: {str(e)}",
                    "message": "",
                    "data": {},
                }
                return Response(error, status=status.HTTP_400_BAD_REQUEST)

        cache = core.api.utils.variants.VariantProcessingCache()
        variant_in_sample_objects: list[core.models.VariantInSample] = []
        variant_annotation_objects: list[core.models.VariantAnnotation] = []
        pending_annotation_keys: set[tuple[str, str, str]] = set()

        def flush_chunk():
            if variant_in_sample_objects:
                core.models.VariantInSample.objects.bulk_create(
                    variant_in_sample_objects, batch_size=CHUNK_SIZE
                )
                variant_in_sample_objects.clear()
            if variant_annotation_objects:
                core.models.VariantAnnotation.objects.bulk_create(
                    variant_annotation_objects, batch_size=CHUNK_SIZE
                )
                variant_annotation_objects.clear()
            pending_annotation_keys.clear()
            cache.reset()

        with transaction.atomic():
            for v_data in data["variants"]:
                split_data = core.api.utils.variants.split_variant_data(
                    v_data,
                    sample_obj,
                    data["bioinformatics_analysis_date"],
                    cache=cache,
                )
                if "ERROR" in split_data:
                    return Response(
                        {
                            "ERROR": split_data,
                            "message": "error extracting variant data from request.data",
                            "data": {},
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                variant_in_sample_data = split_data["variant_in_sample"]
                try:
                    variant_id = int(variant_in_sample_data["variantID_id"])
                except (ValueError, TypeError) as exc:
                    return Response(
                        {
                            "ERROR": f"Invalid variantID_id value: {variant_in_sample_data.get('variantID_id')}",
                            "message": str(exc),
                            "data": {},
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                variant_kwargs = {
                    key: value
                    for key, value in variant_in_sample_data.items()
                    if key != "variantID_id"
                }
                variant_kwargs["sampleID_id"] = sample_obj
                variant_kwargs["variantID_id_id"] = variant_id

                variant_in_sample_objects.append(
                    core.models.VariantInSample(**variant_kwargs)
                )

                ann_data = split_data["variant_ann"].copy()
                ann_key = (
                    cache._norm(ann_data.get("hgvs_c")),
                    cache._norm(ann_data.get("hgvs_p")),
                    cache._norm(ann_data.get("hgvs_p_1_letter")),
                )

                if ann_key in pending_annotation_keys:
                    continue

                if core.api.utils.variants.variant_annotation_exists(
                    ann_data, cache=cache
                ):
                    continue

                cache.cache_annotation(
                    ann_data.get("hgvs_c"),
                    ann_data.get("hgvs_p"),
                    ann_data.get("hgvs_p_1_letter"),
                )
                pending_annotation_keys.add(ann_key)
                ann_kwargs = {
                    key: value
                    for key, value in ann_data.items()
                    if key not in {"variantID_id", "geneID_id", "effectID_id"}
                }
                ann_kwargs["variantID_id_id"] = variant_id
                ann_kwargs["geneID_id_id"] = ann_data.get("geneID_id")
                ann_kwargs["effectID_id_id"] = ann_data.get("effectID_id")
                variant_annotation_objects.append(
                    core.models.VariantAnnotation(**ann_kwargs)
                )

                if len(variant_in_sample_objects) >= CHUNK_SIZE:
                    flush_chunk()
            flush_chunk()

        sample_obj.update_state("Variant")
        # Include date and state in DateState table
        state_id = (
            core.models.SampleState.objects.filter(state__exact="Variant")
            .last()
            .get_state_id()
        )
        sample_id = sample_obj.get_sample_id()
        core.api.utils.common_functions.update_change_state_date(sample_id, state_id)

        return Response(
            {"message": "Successfully updated variant data", "data": {}},
            status=status.HTTP_201_CREATED,
        )
    else:
        return Response(
            {"ERROR": "Invalid request method, use POST", "message": "", "data": {}},
            status=status.HTTP_400_BAD_REQUEST,
        )


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
        allow_null=True,
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
        sample_obj = core.utils.samples.get_sample_obj_from_sample_name(
            data["sample_name"]
        )
        if sample_obj is None:
            error = {
                "ERROR": core.config.ERROR_SAMPLE_NOT_DEFINED,
                "message": "",
                "data": {},
            }
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
        sample_id = sample_obj.get_sample_id()
        # if state exists,
        if core.models.SampleState.objects.filter(state=data["state"]).exists():
            s_data = {
                "state": core.models.SampleState.objects.filter(state=data["state"])
                .last()
                .get_state_id()
            }
        else:
            return Response(
                {
                    "ERROR": f"state {data['state']} does not exist in database",
                    "message": "",
                    "data": {},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        sample_serializer = core.api.serializers.UpdateStateSampleSerializer(
            sample_obj, data=s_data
        )
        if not sample_serializer.is_valid():
            return Response(
                {"ERROR": sample_serializer.errors, "message": "", "data": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sample_serializer.save()

        if "error_type" in data and "Error" in data["state"]:
            error_type_id = (
                core.models.Error.objects.filter(error_name=data["error_type"])
                .last()
                .get_error_id()
            )
            e_data = {"error_type": error_type_id}
            sample_err_serializer = core.api.serializers.CreateErrorSerializer(
                sample_obj, data=e_data
            )
            if not sample_err_serializer.is_valid():
                return Response(
                    {"ERROR": sample_err_serializer.errors, "message": "", "data": {}},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            sample_err_serializer.save()

        core.api.utils.common_functions.update_change_state_date(
            sample_id, s_data["state"]
        )

        return Response(
            {"message": "Successful. sample state updated", "data": {}},
            status=status.HTTP_201_CREATED,
        )
    return Response(
        {"ERROR": "Invalid request method, use PUT", "message": "", "data": {}},
        status=status.HTTP_400_BAD_REQUEST,
    )


@authentication_classes([SessionAuthentication, BasicAuthentication])
@permission_classes([IsAuthenticated])
@api_view(["GET"])
def check_sample_exists(request):
    if request.method != "GET":
        return Response(
            {"ERROR": "Invalid request method, use GET", "message": "", "data": {}},
            status=status.HTTP_400_BAD_REQUEST,
        )
    data = request.query_params
    lab_code_field = "collecting_institution_code_1"
    lab_code_raw = data.get(lab_code_field)
    lab_code_value = str(lab_code_raw).strip() if lab_code_raw else ""
    collecting_institution = data.get("collecting_institution", "").strip()
    resolved_collecting_name = core.utils.lab_catalog.ensure_lab_display(
        lab_code_value, fallback_name=collecting_institution
    )

    required_dict = {
        "sequencing_sample_id": data.get("sequencing_sample_id"),
        "collecting_lab_sample_id": data.get("collecting_lab_sample_id"),
        "submitting_institution": data.get("submitting_institution"),
        "collecting_institution": resolved_collecting_name or collecting_institution,
    }
    if not all(required_dict.values()):
        missing_fields = [x for x, v in required_dict.items() if not v]
        return Response(
            {
                "ERROR": f"Missing required fields in data: {missing_fields}",
                "message": "",
                "data": {},
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    temp_fingerprint = core.utils.samples.build_sample_fingerprint(
        *[value for value in required_dict.values()]
    )
    found_sample = core.utils.samples.get_sample_obj_from_fingerprint(temp_fingerprint)
    if found_sample:
        return Response(
            {"message": "sample correctly found", "data": found_sample},
            status=status.HTTP_200_OK,
        )
    else:
        return Response(
            {"message": "Sample not found.", "data": {}}, status=status.HTTP_200_OK
        )
