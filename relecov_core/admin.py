from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from relecov_core.models import (
    Analysis,
    Authors,
    Caller,
    Chromosome,
    ConfigSetting,
    Document,
    Effect,
    Gene,
    Lineage,
    Filter,
    Profile,
    PublicDatabase,
    PublicDatabaseField,
    Sample,
    Variant,
    QcStats,
    SampleState,
    Schema,
    SchemaProperties,
    PropertyOptions,
    Metadata,
    MetadataProperties,
)


class ProfileInLine(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInLine,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "uploadedFile"]


class CallerAdmin(admin.ModelAdmin):
    list_display = ["name", "version"]


class ConfigSettingAdmin(admin.ModelAdmin):
    list_display = ["configuration_name", "configuration_value"]


class FilterAdmin(admin.ModelAdmin):
    list_display = ["filter"]


class EffectAdmin(admin.ModelAdmin):
    list_display = ["effect", "hgvs_c", "hgvs_p", "hgvs_p_1_letter"]


class LineageAdmin(admin.ModelAdmin):
    list_display = [
        "lineage_identification_date",
        "lineage_name",
        "lineage_analysis_software_name",
        "if_lineage_identification_other",
        "lineage_analysis_software_version",
    ]


class GeneAdmin(admin.ModelAdmin):
    list_display = ["gene"]


class ChromosomeAdmin(admin.ModelAdmin):
    list_display = ["chromosome"]


class SampleAdmin(admin.ModelAdmin):
    list_display = [
        "collecting_lab_sample_id",
        "sequencing_sample_id",
        "biosample_accession_ENA",
        "virus_name",
        "gisaid_id",
        "sequencing_date",
    ]


class SampleStateAdmin(admin.ModelAdmin):
    list_display = ["state", "description"]


class VariantAdmin(admin.ModelAdmin):
    list_display = ["pos", "ref", "alt", "dp", "alt_dp", "ref_dp", "af"]


class AnalysisAdmin(admin.ModelAdmin):
    list_display = [
        "raw_sequence_data_processing_method",
        # "dehosting_method",
        # "dehosting_software_name",
        # "dehosting_software_version",
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


class SchemaAdmin(admin.ModelAdmin):
    list_display = [
        "schema_name",
        "schema_version",
        "schema_default",
        "schema_in_use",
        "schema_apps_name",
    ]


class SchemaPropertiesAdmin(admin.ModelAdmin):
    list_display = ["schemaID", "property", "label", "required"]


class PropertyOptionsAdmin(admin.ModelAdmin):
    list_display = ["propertyID", "enums", "ontology"]


class MetadataAdmin(admin.ModelAdmin):
    list_display = [
        "metadata_name",
        "metadata_version",
        "metadata_default",
        "metadata_in_use",
        "metadata_apps_name",
    ]


class MetadataPropertiesAdmin(admin.ModelAdmin):
    list_display = [
        "metadataID",
        "property",
        "label",
        "order",
        "fill_mode",
    ]


# Register models
admin.site.register(Document, DocumentAdmin)
admin.site.register(Caller, CallerAdmin)
admin.site.register(ConfigSetting, ConfigSettingAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(Effect, EffectAdmin)
admin.site.register(Lineage, LineageAdmin)
admin.site.register(Gene, GeneAdmin)
admin.site.register(Chromosome, ChromosomeAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(SampleState, SampleStateAdmin)
admin.site.register(Variant, VariantAdmin)
admin.site.register(Analysis, AnalysisAdmin)
admin.site.register(QcStats, QcStatsAdmin)
admin.site.register(Authors, AuthorsAdmin)
admin.site.register(PublicDatabase, PublicDatabaseAdmin)
admin.site.register(PublicDatabaseField, PublicDatabaseFieldAdmin)
admin.site.register(Schema, SchemaAdmin)
admin.site.register(SchemaProperties, SchemaPropertiesAdmin)
admin.site.register(PropertyOptions, PropertyOptionsAdmin)
admin.site.register(Metadata, MetadataAdmin)
admin.site.register(MetadataProperties, MetadataPropertiesAdmin)
