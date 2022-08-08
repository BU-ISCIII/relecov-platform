from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from relecov_core.models import (
    Authors,
    BioInfoAnalysisValue,
    BioinfoAnalysisField,
    Caller,
    Classification,
    Chromosome,
    ConfigSetting,
    Document,
    Effect,
    EnaInfo,
    Error,
    Gene,
    GisaidInfo,
    Filter,
    # Lineage,
    LineageInfo,
    MetadataVisualization,
    Position,
    Profile,
    PropertyOptions,
    Sample,
    SampleState,
    Schema,
    SchemaProperties,
    TemporalSampleStorage,
    Variant,
    VariantInSample,
    DateUpdateState,
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


class BioinfoAnalysisFielddAdmin(admin.ModelAdmin):
    list_display = ["property_name", "classificationID", "label_name"]
    search_fields = ("property_name__icontains",)


class BioInfoAnalysisValueAdmin(admin.ModelAdmin):
    list_display = ["value", "bioinfo_analysis_fieldID", "sampleID_id"]
    search_fields = ("value__icontains",)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "uploadedFile"]


class CallerAdmin(admin.ModelAdmin):
    list_display = ["name", "version"]


class ClassificationAdmin(admin.ModelAdmin):
    list_display = ["classification_name"]


class ConfigSettingAdmin(admin.ModelAdmin):
    list_display = ["configuration_name", "configuration_value"]


class EffectAdmin(admin.ModelAdmin):
    list_display = ["effect", "hgvs_c", "hgvs_p", "hgvs_p_1_letter"]


class EnaInfoAdmin(admin.ModelAdmin):
    list_display = ["biosample_accession_ENA", "SRA_accession", "study_title"]


class FilterAdmin(admin.ModelAdmin):
    list_display = ["filter"]


class GeneAdmin(admin.ModelAdmin):
    list_display = ["gene"]


class GisaidInfoAdmin(admin.ModelAdmin):
    list_display = ["gisaid_id", "submission_data"]


class ChromosomeAdmin(admin.ModelAdmin):
    list_display = ["chromosome"]


class LineageInfoAdmin(admin.ModelAdmin):
    list_display = ["lineage_name"]


class LineageAdmin(admin.ModelAdmin):
    list_display = [
        "lineage_name",
        "lineage_analysis_software_name",
        "lineage_analysis_software_version",
    ]


class PositionAdmin(admin.ModelAdmin):
    list_display = ["pos", "nucleotide"]


class SampleAdmin(admin.ModelAdmin):
    list_display = [
        "sequencing_sample_id",
        "submitting_lab_sample_id",
        "state",
    ]
    search_fields = ["sequencing_sample_id__icontains"]
    list_filter = ["created_at"]


class SampleStateAdmin(admin.ModelAdmin):
    list_display = ["state", "description"]


class VariantAdmin(admin.ModelAdmin):
    list_display = ["ref"]


class VariantInSampleAdmin(admin.ModelAdmin):
    list_display = ["dp", "alt_dp", "ref_dp", "af"]


class AuthorsAdmin(admin.ModelAdmin):
    list_display = ["analysis_authors", "author_submitter", "authors"]


class SchemaAdmin(admin.ModelAdmin):
    list_display = [
        "schema_name",
        "schema_version",
        "schema_default",
        "schema_in_use",
        "schema_apps_name",
    ]


class SchemaPropertiesAdmin(admin.ModelAdmin):
    list_display = ["property", "label", "schemaID", "required"]
    search_fields = ["property__icontains"]


class TemporalSampleStorageAdmin(admin.ModelAdmin):
    list_display = ["sample_idx", "field", "value", "sent"]


class PropertyOptionsAdmin(admin.ModelAdmin):
    list_display = ["propertyID", "enums", "ontology"]


class MetadataVisualizationAdmin(admin.ModelAdmin):
    list_display = [
        "property_name",
        "label_name",
        "fill_mode",
        "in_use",
    ]


# Register models
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Document, DocumentAdmin)
admin.site.register(Caller, CallerAdmin)
admin.site.register(ConfigSetting, ConfigSettingAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(Effect, EffectAdmin)
admin.site.register(EnaInfo, EnaInfoAdmin)
admin.site.register(Gene, GeneAdmin)
admin.site.register(GisaidInfo, GisaidInfoAdmin)
admin.site.register(Chromosome, ChromosomeAdmin)
# admin.site.register(Lineage, LineageAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(SampleState, SampleStateAdmin)
admin.site.register(Variant, VariantAdmin)
admin.site.register(VariantInSample, VariantInSampleAdmin)
admin.site.register(Authors, AuthorsAdmin)
admin.site.register(Schema, SchemaAdmin)
admin.site.register(SchemaProperties, SchemaPropertiesAdmin)
admin.site.register(PropertyOptions, PropertyOptionsAdmin)
admin.site.register(MetadataVisualization, MetadataVisualizationAdmin)

admin.site.register(BioinfoAnalysisField, BioinfoAnalysisFielddAdmin)
admin.site.register(BioInfoAnalysisValue, BioInfoAnalysisValueAdmin)
admin.site.register(Classification, ClassificationAdmin)
admin.site.register(TemporalSampleStorage, TemporalSampleStorageAdmin)
admin.site.register(Error)
admin.site.register(DateUpdateState)
admin.site.register(LineageInfo, LineageInfoAdmin)
