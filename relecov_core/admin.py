from django.contrib import admin
from .models import *


class CallerAdmin(admin.ModelAdmin):
    list_display = ["name", "version"]


class FilterAdmin(admin.ModelAdmin):
    list_display = ["filter"]


class EffectAdmin(admin.ModelAdmin):
    list_display = ["effect", "hgvs_c", "hgvs_p", "hgvs_p_1_letter"]


class LineageAdmin(admin.ModelAdmin):
    list_display = ["lineage", "week"]


class GeneAdmin(admin.ModelAdmin):
    list_display = ["gene"]


class ChromosomeAdmin(admin.ModelAdmin):
    list_display = ["chromosome"]


class SampleAdmin(admin.ModelAdmin):
    list_display = [
        "collecting_lab_sample_id", "sequencing_sample_id", "biosample_accession_ENA", "virus_name",
        "gisaid_id", "sequencing_date", "public_health_sample_id_sivies", "submitting_lab_sample_id",
        "microbiology_lab_sample_id", "isolate_sample_id", "collecting_institution", "sample_collection_date",
        "sample_received_date", "anatomical_material", "environmental_material", "host_age", "host_gender",
        "sequence_file_R1_fastq", "sequence_file_R2_fastq"
        ]

class SampleOtherAdmin(admin.ModelAdmin):
    list_display = [
    "sample_storage_conditions", "collection_device", "rna_extraction_Protocol", "library_kit", "library_preparation_kit"
    ]
         

class VariantAdmin(admin.ModelAdmin):
    list_display = ["pos", "ref", "alt", "dp", "alt_dp", "ref_dp", "af"]


class AnalysisAdmin(admin.ModelAdmin):
    list_display = [
        "raw_sequence_data_processing_method",
        "dehosting_method",
        "assembly",
        "if_assembly_other",
        "assembly_params",
        "variant_calling",
        "if_variant_calling_other",
        "variant_calling_params",
        "consensus_sequence_name",
        "consensus_sequence_name_md5",
        "consensus_sequence_filepath",
        "consensus_sequence_software_name",
        "if_consensus_other",
        "consensus_sequence_software_version",
        "consensus_criteria",
        "reference_genome_accession",
        "bioinformatics_protocol",
        "if_bioinformatic_protocol_is_other_specify",
        "bioinformatic_protocol_version",
        "analysis_date",
        "commercial_open_source_both",
        "preprocessing",
        "if_preprocessing_other",
        "preprocessing_params",
        "mapping",
        "if_mapping_other",
        "mapping_params",
        "reference_genome_accession",
    ]


class QcStatsAdmin(admin.ModelAdmin):
    list_display = [
        "quality_control_metrics",
        "breadth_of_coverage_value",
        "depth_of_coverage_value",
        "depth_of_coverage_threshold",
        "number_of_base_pairs_sequenced",
        "consensus_genome_length",
        "ns_per_100_kbp",
        "per_qc_filtered",
        "per_reads_host",
        "per_reads_virus",
        "per_unmapped",
        "per_genome_greater_10x",
        "mean_depth_of_coverage_value",
        "per_Ns",
        "number_of_variants_AF_greater_75percent",
        "number_of_variants_with_effect",
    ]


class AuthorsAdmin(admin.ModelAdmin):
    list_display = ["analysis_authors", "author_submitter", "authors"]


class PublicDatabaseAdmin(admin.ModelAdmin):
    list_display = ["databaseName"]
    
    
class PublicDatabaseFieldAdmin(admin.ModelAdmin):
    list_display = ["publicDatabaseID", "fieldName", "fieldDescription", "fieldInUse"]


# Register models
admin.site.register(Caller, CallerAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(Effect, EffectAdmin)
admin.site.register(Lineage, LineageAdmin)
admin.site.register(Gene, GeneAdmin)
admin.site.register(Chromosome, ChromosomeAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(Variant, VariantAdmin)
admin.site.register(Analysis, AnalysisAdmin)
admin.site.register(QcStats, QcStatsAdmin)
admin.site.register(Authors, AuthorsAdmin)
admin.site.register(PublicDatabase, PublicDatabaseAdmin)
admin.site.register(PublicDatabaseField, PublicDatabaseFieldAdmin)
admin.site.register(SampleOther, SampleOtherAdmin) #Duplicada de momento

# admin.site.register(Lineage, LineageAdmin) #Duplicada de momento
# admin.site.register(LineageOrOptional, LineageOrOptionalAdmin) #No definida de momento




"""  
#Duplicada de momento  
class SampleAdmin(admin.ModelAdmin):
    list_display = ["collecting_lab_sample_id", "sequencing_sample_id", "biosample_accession_ENA", "virus_name", "gisaid_id", "sequencing_date"]
"""

"""    
#Duplicada de momento
class LineageAdmin(admin.ModelAdmin):
    list_display = ["lineage_identification_date", "lineage_name", "lineage_analysis_software_name", 
                    "if_lineage_identification_other", "lineage_analysis_software_version"]
"""

""" 
#No definida de momento   
class LineageOrOptionalAdmin(admin.ModelAdmin):
    list_display = []
"""

"""
class PublicDatabaseAdmin(admin.ModelAdmin):
    list_display = [
        "library_selection",
        "library_strategy",
        "library_layout",
        "analysis_accession",
        "study_accession",
        "secondary_study_accession",
        "sample_accession",
        "secondary_sample_accession",
        "experiment_accession",
        "run_accession",
        "submission_accession",
        "read_count",
        "read_length",
        "base_count",
        "center_name",
        "first_public",
        "last_updated",
        "experiment_title",
        "study_title",
        "study_alias",
        "experiment_alias",
        "run_alias",
        "fastq_bytes",
        "fastq_md5_r1",
        "fastq_md5_r2",
        "fastq_ftp",
        "fastq_aspera",
        "fastq_galaxy",
        "submitted_bytes",
        "submitted_md5",
        "submitted_ftp",
        "submitted_aspera",
        "submitted_galaxy",
        "submitted_format",
        "sra_bytes",
        "sra_md5",
        "sra_ftp",
        "sra_aspera",
        "sra_galaxy",
        "broker_name",
        "nominal_sdev",
        "first_created_date",
    ]
"""


