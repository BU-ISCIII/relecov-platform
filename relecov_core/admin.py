from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from relecov_core.models import (
    BioInfoAnalysisValue,
    BioinfoAnalysisField,
    Classification,
    Chromosome,
    ConfigSetting,
    Effect,
    Error,
    Gene,
    Filter,
    LineageFields,
    LineageValues,
    LineageInfo,
    MetadataVisualization,
    OrganismAnnotation,
    # Position,
    Profile,
    PropertyOptions,
    PublicDatabaseFields,
    PublicDatabaseValues,
    PublicDatabaseType,
    Sample,
    SampleState,
    Schema,
    SchemaProperties,
    TemporalSampleStorage,
    Variant,
    VariantInSample,
    VariantAnnotation,
    DateUpdateState,
)


def custom_date_format(self):
    if self.date:
        return self.date.strftime("%d %b %Y")
    return ""


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


class AnalysisPerformedAdmin(admin.ModelAdmin):
    list_display = ["typeID", "sampleID"]


class BioinfoAnalysisFielddAdmin(admin.ModelAdmin):
    list_display = ["property_name", "label_name"]
    search_fields = ("property_name__icontains",)


class BioInfoAnalysisValueAdmin(admin.ModelAdmin):
    list_display = ["value", "bioinfo_analysis_fieldID"]
    search_fields = ("value__icontains",)


class ClassificationAdmin(admin.ModelAdmin):
    list_display = ["classification_name"]


class ConfigSettingAdmin(admin.ModelAdmin):
    list_display = ["configuration_name", "configuration_value"]


class DateUpdateStateAdmin(admin.ModelAdmin):
    list_display = ["sampleID", "stateID", custom_date_format]


class EffectAdmin(admin.ModelAdmin):
    list_display = ["effect"]


class ErrorAdmin(admin.ModelAdmin):
    list_display = ["error_name", "display_string"]


class FilterAdmin(admin.ModelAdmin):
    list_display = ["filter"]


class GeneAdmin(admin.ModelAdmin):
    list_display = ["gene_name", "gene_start", "gene_end", "org_annotationID"]


class ChromosomeAdmin(admin.ModelAdmin):
    list_display = ["chromosome"]


class LineageInfoAdmin(admin.ModelAdmin):
    list_display = ["lineage_name"]


class LineageFieldsAdmin(admin.ModelAdmin):
    list_display = ["property_name", "label_name"]


class LineageValuesAdmin(admin.ModelAdmin):
    list_display = ["value", "lineage_fieldID"]


class OrganismAnnotationAdmin(admin.ModelAdmin):
    list_display = ["organism_code", "gff_version", "sequence_region"]


class PublicDatabaseTypeAdmin(admin.ModelAdmin):
    list_display = ["public_type_name", "public_type_display"]


class PublicDatabaseFieldsAdmin(admin.ModelAdmin):
    list_display = ["property_name", "database_type"]


class PublicDatabaseValuesAdmin(admin.ModelAdmin):
    list_display = ["value", "sampleID", "public_database_fieldID"]


class SampleAdmin(admin.ModelAdmin):
    list_display = [
        "sequencing_sample_id",
        "submitting_lab_sample_id",
        "collecting_lab_sample_id",
        "state",
    ]
    search_fields = ["sequencing_sample_id__icontains"]
    list_filter = ["created_at"]


class SampleStateAdmin(admin.ModelAdmin):
    list_display = ["state", "description"]


class VariantAdmin(admin.ModelAdmin):
    list_display = [
        "pos",
        "ref",
        "alt",
        "chromosomeID_id",
        "filterID_id",
    ]


class VariantInSampleAdmin(admin.ModelAdmin):
    list_display = ["sampleID_id", "variantID_id", "dp", "alt_dp", "ref_dp", "af"]


class VariantAnnotationAdmin(admin.ModelAdmin):
    list_display = ["variantID_id", "geneID_id", "hgvs_c", "hgvs_p", "hgvs_p_1_letter"]


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
    list_display = ["propertyID", "enum", "ontology"]


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
admin.site.register(ConfigSetting, ConfigSettingAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(Effect, EffectAdmin)
admin.site.register(Gene, GeneAdmin)
admin.site.register(Chromosome, ChromosomeAdmin)
admin.site.register(LineageFields, LineageFieldsAdmin)
admin.site.register(LineageValues, LineageValuesAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(SampleState, SampleStateAdmin)
admin.site.register(Variant, VariantAdmin)
admin.site.register(VariantInSample, VariantInSampleAdmin)
admin.site.register(VariantAnnotation, VariantAnnotationAdmin)
admin.site.register(Schema, SchemaAdmin)
admin.site.register(SchemaProperties, SchemaPropertiesAdmin)
admin.site.register(PropertyOptions, PropertyOptionsAdmin)
admin.site.register(PublicDatabaseType, PublicDatabaseTypeAdmin)
admin.site.register(PublicDatabaseFields, PublicDatabaseFieldsAdmin)
admin.site.register(PublicDatabaseValues, PublicDatabaseValuesAdmin)
admin.site.register(MetadataVisualization, MetadataVisualizationAdmin)
admin.site.register(BioinfoAnalysisField, BioinfoAnalysisFielddAdmin)
admin.site.register(BioInfoAnalysisValue, BioInfoAnalysisValueAdmin)
admin.site.register(Classification, ClassificationAdmin)
admin.site.register(TemporalSampleStorage, TemporalSampleStorageAdmin)
admin.site.register(Error, ErrorAdmin)
admin.site.register(DateUpdateState, DateUpdateStateAdmin)
admin.site.register(LineageInfo, LineageInfoAdmin)
admin.site.register(OrganismAnnotation, OrganismAnnotationAdmin)
