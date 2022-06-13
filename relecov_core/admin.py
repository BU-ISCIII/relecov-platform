from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from relecov_core.models import (
    Authors,
    BioInfoProcessValue,
    BioinfoProcessField,
    Caller,
    Classification,
    Chromosome,
    ConfigSetting,
    Document,
    Effect,
    Gene,
    Filter,
    MetadataVisualization,
    Position,
    Profile,
    PropertyOptions,
    PublicDatabase,
    Sample,
    SampleState,
    Schema,
    SchemaProperties,
    TemporalSampleStorage,
    Variant,
    VariantInSample,
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


class BioinfoProcessFieldAdmin(admin.ModelAdmin):
    list_display = ["property_name", "classificationID", "label_name"]
    search_fields = ("property_name__icontains",)


class BioinfoProcessValueAdmin(admin.ModelAdmin):
    list_display = ["value", "bioinfo_process_fieldID", "sampleID_id"]
    search_fields = ("value__icontains",)


class DocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "uploadedFile"]


class CallerAdmin(admin.ModelAdmin):
    list_display = ["name", "version"]


class ClassificationAdmin(admin.ModelAdmin):
    list_display = ["class_name"]


class ConfigSettingAdmin(admin.ModelAdmin):
    list_display = ["configuration_name", "configuration_value"]


class FilterAdmin(admin.ModelAdmin):
    list_display = ["filter"]


class EffectAdmin(admin.ModelAdmin):
    list_display = ["effect", "hgvs_c", "hgvs_p", "hgvs_p_1_letter"]


class GeneAdmin(admin.ModelAdmin):
    list_display = ["gene"]


class ChromosomeAdmin(admin.ModelAdmin):
    list_display = ["chromosome"]


# class LineageAdmin(admin.ModelAdmin):
#    list_display = ["lineage_name"]


class PositionAdmin(admin.ModelAdmin):
    list_display = ["pos", "nucleotide"]


class SampleAdmin(admin.ModelAdmin):
    list_display = [
        "sequencing_sample_id",
        "submitting_lab_sample_id",
        "state",
    ]


class SampleStateAdmin(admin.ModelAdmin):
    list_display = ["state", "description"]


class VariantAdmin(admin.ModelAdmin):
    list_display = ["ref"]


class VariantInSampleAdmin(admin.ModelAdmin):
    list_display = ["dp", "alt_dp", "ref_dp", "af"]


class AuthorsAdmin(admin.ModelAdmin):
    list_display = ["analysis_authors", "author_submitter", "authors"]


class PublicDatabaseAdmin(admin.ModelAdmin):
    list_display = ["databaseName"]


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
admin.site.register(BioinfoProcessField, BioinfoProcessFieldAdmin)
admin.site.register(BioInfoProcessValue, BioinfoProcessValueAdmin)
admin.site.register(Caller, CallerAdmin)
admin.site.register(Classification, ClassificationAdmin)
admin.site.register(ConfigSetting, ConfigSettingAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(Effect, EffectAdmin)
admin.site.register(Gene, GeneAdmin)
admin.site.register(Chromosome, ChromosomeAdmin)
# admin.site.register(Lineage, LineageAdmin)
admin.site.register(Position, PositionAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(SampleState, SampleStateAdmin)
admin.site.register(Variant, VariantAdmin)
admin.site.register(VariantInSample, VariantInSampleAdmin)
admin.site.register(Authors, AuthorsAdmin)
admin.site.register(PublicDatabase, PublicDatabaseAdmin)
admin.site.register(Schema, SchemaAdmin)
admin.site.register(SchemaProperties, SchemaPropertiesAdmin)
admin.site.register(TemporalSampleStorage, TemporalSampleStorageAdmin)
admin.site.register(PropertyOptions, PropertyOptionsAdmin)
admin.site.register(MetadataVisualization, MetadataVisualizationAdmin)
