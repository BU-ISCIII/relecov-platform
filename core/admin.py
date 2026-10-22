# Generic imports
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django import forms
import os

# Local imports
import core.models


def custom_date_format(self):
    if self.date:
        return self.date.strftime("%d %b %Y")
    return ""


class ProfileInLine(admin.StackedInline):
    model = core.models.Profile
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


class BioinfoAnalysisValueAdmin(admin.ModelAdmin):
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
    list_display = ["gene_name", "gene_start", "gene_end", "chromosomeID"]


class ChromosomeAdmin(admin.ModelAdmin):
    list_display = ["chromosome"]


class LineageInfoAdmin(admin.ModelAdmin):
    list_display = ["lineage_assignment"]


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
    search_fields = ["value__icontains", "sampleID__sequencing_sample_id__icontains"]


class SampleAdmin(admin.ModelAdmin):
    list_display = [
        "sequencing_sample_id",
        "submitting_lab_sample_id",
        "collecting_lab_sample_id",
        "state",
    ]
    search_fields = ["sequencing_sample_id__icontains"]
    list_filter = ["created_at"]
    exclude = ("lineage_values", "lineage_info", "bio_analysis_values")


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


class SchemaAdminForm(forms.ModelForm):
    json_content = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = core.models.Schema
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.file_name:
            path = self.instance.file_name.path
            if os.path.exists(path):
                if self.instance and self.instance.file_name:
                    f = self.instance.file_name
                    try:
                        f.open()  # opens file in storage backend
                        self.fields["json_content"].initial = f.read().decode("utf-8")
                        f.close()
                    except Exception:
                        self.fields["json_content"].initial = ""
            else:
                print(f"Schema file does not exist: {path}")

    def save(self, commit=True):
        instance = super().save(commit=False)
        content = self.cleaned_data.get("json_content")
        if content:
            with open(instance.file_name.path, "w") as f:
                f.write(content)
        if commit:
            instance.save()
        return instance


class SchemaAdmin(admin.ModelAdmin):
    form = SchemaAdminForm
    list_display = [
        "schema_name",
        "schema_version",
        "schema_default",
        "schema_in_use",
        "schema_apps_name",
    ]
    search_fields = ["schema_name", "schema_version", "schema_apps_name"]
    list_filter = ["schema_in_use", "schema_default", "schema_apps_name"]


class SchemaPropertiesAdmin(admin.ModelAdmin):
    list_display = ["property", "label", "schemaID", "required"]
    search_fields = ["property__icontains"]


class TemporalSampleStorageAdmin(admin.ModelAdmin):
    list_display = ["sample_name", "field", "value", "user"]


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
admin.site.register(core.models.ConfigSetting, ConfigSettingAdmin)
admin.site.register(core.models.Filter, FilterAdmin)
admin.site.register(core.models.Effect, EffectAdmin)
admin.site.register(core.models.Gene, GeneAdmin)
admin.site.register(core.models.Chromosome, ChromosomeAdmin)
admin.site.register(core.models.LineageFields, LineageFieldsAdmin)
admin.site.register(core.models.LineageValues, LineageValuesAdmin)
admin.site.register(core.models.Sample, SampleAdmin)
admin.site.register(core.models.SampleState, SampleStateAdmin)
admin.site.register(core.models.Variant, VariantAdmin)
admin.site.register(core.models.VariantInSample, VariantInSampleAdmin)
admin.site.register(core.models.VariantAnnotation, VariantAnnotationAdmin)
admin.site.register(core.models.Schema, SchemaAdmin)
admin.site.register(core.models.SchemaProperties, SchemaPropertiesAdmin)
admin.site.register(core.models.PropertyOptions, PropertyOptionsAdmin)
admin.site.register(core.models.PublicDatabaseType, PublicDatabaseTypeAdmin)
admin.site.register(core.models.PublicDatabaseFields, PublicDatabaseFieldsAdmin)
admin.site.register(core.models.PublicDatabaseValues, PublicDatabaseValuesAdmin)
admin.site.register(core.models.MetadataVisualization, MetadataVisualizationAdmin)
admin.site.register(core.models.BioinfoAnalysisField, BioinfoAnalysisFielddAdmin)
admin.site.register(core.models.BioinfoAnalysisValue, BioinfoAnalysisValueAdmin)
admin.site.register(core.models.Classification, ClassificationAdmin)
admin.site.register(core.models.TemporalSampleStorage, TemporalSampleStorageAdmin)
admin.site.register(core.models.Error, ErrorAdmin)
admin.site.register(core.models.DateUpdateState, DateUpdateStateAdmin)
admin.site.register(core.models.LineageInfo, LineageInfoAdmin)
admin.site.register(core.models.OrganismAnnotation, OrganismAnnotationAdmin)
