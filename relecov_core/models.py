from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from relecov_core.core_config import (
    SCHEMAS_UPLOAD_FOLDER,
    METADATA_UPLOAD_FOLDER,
)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    laboratory = models.CharField(max_length=60, null=True, blank=True)

    class Meta:
        db_table = "Profile"

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()


class Document(models.Model):
    title = models.CharField(max_length=200)
    file_path = models.CharField(max_length=200)
    uploadedFile = models.FileField(upload_to=METADATA_UPLOAD_FOLDER)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Document"

    def __str__(self):
        return "%s" % (self.title)


class SchemaManager(models.Manager):
    def create_new_schema(self, data):
        new_schema = self.create(
            file_name=data["file_name"],
            user_name=data["user_name"],
            schema_name=data["schema_name"],
            schema_version=data["schema_version"],
            schema_default=data["schema_default"],
            schema_in_use=True,
            schema_apps_name=data["schema_app_name"],
        )
        return new_schema


class Schema(models.Model):
    file_name = models.FileField(upload_to=SCHEMAS_UPLOAD_FOLDER)
    user_name = models.ForeignKey(User, on_delete=models.CASCADE)
    schema_name = models.CharField(max_length=40)
    schema_version = models.CharField(max_length=10)
    schema_in_use = models.BooleanField(default=True)
    schema_default = models.BooleanField(default=True)
    schema_apps_name = models.CharField(max_length=40, null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = "Schema"

    def __str__(self):
        return "%s_%s" % (self.schema_name, self.schema_version)

    def get_schema_and_version(self):
        return "%s_%s" % (self.schema_name, self.schema_version)

    def get_schema_name(self):
        return "%s" % (self.schema_name)

    def get_schema_id(self):
        return "%s" % (self.pk)

    def get_schema_info(self):
        data = []
        data.append(self.pk)
        data.append(self.schema_name)
        data.append(self.schema_version)
        data.append(self.schema_default)
        data.append(str(self.schema_in_use))
        data.append(self.file_name)
        return data

    def update_default(self, default):
        self.schema_default = default
        self.save()

    objects = SchemaManager()


class SchemaPropertiesManager(models.Manager):
    def create_new_property(self, data):
        required = True if "required" in data else False
        options = True if "options" in data else False
        format = data["format"] if "format" in data else None
        new_property_obj = self.create(
            schemaID=data["schemaID"],
            property=data["property"],
            examples=data["examples"],
            ontology=data["ontology"],
            type=data["type"],
            description=data["description"],
            label=data["label"],
            classification=data["classification"],
            fill_mode=data["fill_mode"],
            required=required,
            options=options,
            format=format,
        )
        return new_property_obj


class SchemaProperties(models.Model):
    schemaID = models.ForeignKey(Schema, on_delete=models.CASCADE)
    property = models.CharField(max_length=50)
    examples = models.CharField(max_length=200, null=True, blank=True)
    ontology = models.CharField(max_length=40, null=True, blank=True)
    type = models.CharField(max_length=20)
    format = models.CharField(max_length=20, null=True, blank=True)
    description = models.CharField(max_length=250, null=True, blank=True)
    label = models.CharField(max_length=200, null=True, blank=True)
    classification = models.CharField(max_length=80, null=True, blank=True)
    required = models.BooleanField(default=False)
    options = models.BooleanField(default=False)
    fill_mode = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "SchemaProperties"

    def __str__(self):
        return "%s" % (self.property)

    def get_property_name(self):
        return "%s" % (self.property)

    def get_property_id(self):
        return "%s" % (self.pk)

    def get_property_info(self):
        data = []
        data.append(self.property)
        data.append(self.label)
        data.append(self.required)
        data.append(self.classification)
        data.append(self.description)
        return data

    def has_options(self):
        return self.options

    def get_label(self):
        return "%s" % (self.label)

    def get_format(self):
        return "%s" % (self.format)

    def get_ontology(self):
        return "%s" % (self.ontology)

    objects = SchemaPropertiesManager()


class PropertyOptionsManager(models.Manager):
    def create_property_options(self, data):
        new_property_option_obj = self.create(
            propertyID=data["propertyID"],
            enums=data["enums"],
            ontology=data["ontology"],
        )
        return new_property_option_obj


class PropertyOptions(models.Model):
    propertyID = models.ForeignKey(SchemaProperties, on_delete=models.CASCADE)
    enums = models.CharField(max_length=80, null=True, blank=True)
    ontology = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        db_table = "PropertyOptions"

    def __str__(self):
        return "%s" % (self.enums)

    def get_enum(self):
        return "%s" % (self.enums)

    objects = PropertyOptionsManager()


# Metadata_json
class MetadataVisualizationManager(models.Manager):
    def create_metadata_visualization(self, data):
        new_met_visual = self.create(
            schemaID=data["schema_id"],
            property_name=data["property_name"],
            label_name=data["label_name"],
            order=data["order"],
            in_use=data["in_use"],
            fill_mode=data["fill_mode"],
        )
        return new_met_visual


class MetadataVisualization(models.Model):
    schemaID = models.ForeignKey(Schema, on_delete=models.CASCADE)
    property_name = models.CharField(max_length=60)
    label_name = models.CharField(max_length=80)
    order = models.IntegerField()
    in_use = models.BooleanField(default=True)
    fill_mode = models.CharField(max_length=40)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = "MetadataVisualization"

    def __str__(self):
        return "%s" % (self.label_name)

    def get_label(self):
        return "%s" % (self.label_name)

    def get_property(self):
        return "%s" % (self.property_name)

    def get_order(self):
        return "%s" % (self.order)

    def get_schema_obj(self):
        return self.schemaID

    objects = MetadataVisualizationManager()


class ClassificationManager(models.Manager):
    def create_new_classification(self, class_name):
        new_class_obj = self.create(class_name=class_name)
        return new_class_obj


class Classification(models.Model):
    class_name = models.CharField(max_length=80)

    def __str__(self):
        return "%s" % (self.class_name)

    def get_classification(self):
        return "%s" % (self.class_name)

    objects = ClassificationManager()


class BioinfoProcessFieldManager(models.Manager):
    def create_new_field(self, data):
        new_field = self.create(
            classificationID=data["classificationID"],
            property_name=data["property_name"],
            label_name=data["label_name"],
        )
        return new_field


class BioinfoProcessField(models.Model):
    schemaID = models.ManyToManyField(Schema)
    classificationID = models.ForeignKey(Classification, on_delete=models.CASCADE)
    property_name = models.CharField(max_length=60)
    label_name = models.CharField(max_length=80)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return "%s" % (self.property_name)

    def get_property(self):
        return "%s" % (self.property_name)

    def get_label(self):
        return "%s" % (self.label_name)

    def get_classification_name(self):
        if self.classificationID is not None:
            return self.classificationID.get_classification()
        return None

    objects = BioinfoProcessFieldManager()


# Caller Table
class CallerManager(models.Manager):
    def create_new_caller(self, data):
        new_caller = self.create(name=data["name"], version=data["version"])
        return new_caller


class Caller(models.Model):
    name = models.CharField(max_length=60)
    version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Caller"

    def __str__(self):
        return "%s" % (self.name)

    def get_version(self):
        return "%s" % (self.version)

    objects = CallerManager()


# Filter Table
class FilterManager(models.Manager):
    def create_new_filter(self, data):
        new_filter = self.create(filter=data)
        return new_filter


class Filter(models.Model):
    filter = models.CharField(max_length=70)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Filter"

    def __str__(self):
        return "%s" % (self.filter)

    objects = FilterManager()

    # Effect Table
    """
    fields => SAMPLE(0), CHROM(1), POS(2), REF(3), ALT(4),
    FILTER(5), DP(6),  REF_DP(7), ALT_DP(8), AF(9), GENE(10),
    EFFECT(11), HGVS_C(12), HGVS_P(13), HGVS_P1LETTER(14),
    CALLER(15), LINEAGE(16)
    """


class EffectManager(models.Manager):
    def create_new_effect(self, data):
        new_effect = self.create(
            effect=data[11],
            hgvs_c=data[12],
            hgvs_p=data[13],
            hgvs_p_1_letter=data[14],
        )
        return new_effect


class Effect(models.Model):
    effect = models.CharField(max_length=80)
    hgvs_c = models.CharField(max_length=60)
    hgvs_p = models.CharField(max_length=60)
    hgvs_p_1_letter = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Effect"

    def __str__(self):
        return "%s" % (self.effect)

    def get_hgvs_c(self):
        return "%s" % (self.hgvs_c)

    def get_hgvs_p(self):
        return "%s" % (self.hgvs_p)

    def get_hgvs_p_1_letter(self):
        return "%s" % (self.hgvs_p_1_letter)

    objects = EffectManager()


# Lineage Table
class LineageManager(models.Manager):
    def create_new_Lineage(self, data):
        new_lineage = self.create(
            lineage_identification_date=data["lineage_identification_date"],
            lineage_name=data["lineage_name"],
            lineage_analysis_software_name=data["lineage_analysis_software_name"],
            if_lineage_identification_other=data["if_lineage_identification_other"],
            lineage_analysis_software_version=data["lineage_analysis_software_version"],
        )
        return new_lineage


class Lineage(models.Model):
    lineage_identification_date = models.CharField(max_length=100)
    lineage_name = models.CharField(max_length=100)
    lineage_analysis_software_name = models.CharField(max_length=100)
    if_lineage_identification_other = models.CharField(max_length=100)
    lineage_analysis_software_version = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Lineage"

    def __str__(self):
        return "%s" % (self.lineage_name)

    def get_lineage_identification_date(self):
        return "%s" % (self.lineage_identification_date)

    def get_lineage_name(self):
        return "%s" % (self.lineage_name)

    def get_lineage_analysis_software_name(self):
        return "%s" % (self.lineage_analysis_software_name)

    def get_if_lineage_identification_other(self):
        return "%s" % (self.if_lineage_identification_other)

    def get_lineage_analysis_software_version(self):
        return "%s" % (self.lineage_analysis_software_version)

    objects = LineageManager()


# Gene Table
class GeneManager(models.Manager):
    def create_new_gene(self, data):
        new_gene = self.create(gene=data)
        return new_gene


class Gene(models.Model):
    gene = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Gene"

    def __str__(self):
        return "%s" % (self.gene)

    objects = GeneManager()


# Chromosome Table
class ChromosomeManager(models.Manager):
    def create_new_chromosome(self, data):
        new_chromosome = self.create(chromosome=data)
        return new_chromosome


class Chromosome(models.Model):
    chromosome = models.CharField(max_length=110)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Chromosome"

    def __str__(self):
        return "%s" % (self.chromosome)

    def get_chromosome_id(self):
        return "%s" % (self.pk)

    objects = ChromosomeManager()


# Sample states table
class SampleState(models.Model):
    state = models.CharField(max_length=80)
    display_string = models.CharField(max_length=80, null=True, blank=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "SampleState"

    def __str__(self):
        return "%s" % (self.state)

    def get_state(self):
        return "%s" % (self.description)

    def get_state_id(self):
        return "%s" % (self.pk)


# Sample Table
class SampleManager(models.Manager):
    def create_new_sample(self, data, user):
        state = SampleState.objects.filter(state__exact="pre_recorded").last()
        metadata_file = Document(
            title="title", file_path="file_path", uploadedFile="uploadedFile.xls"
        )
        metadata_file.save()
        if "sequencing_date" not in data:
            data["sequencing_date"] = ""
        new_sample = self.create(
            collecting_lab_sample_id=data,
            sequencing_sample_id=data["sequencing_sample_id"],
            biosample_accession_ENA=data["biosample_accession_ENA"],
            virus_name=data["virus_name"],
            gisaid_id=data["gisaid_id"],
            sequencing_date=data["sequencing_date"],
            # collecting_lab_sample_id=data["collecting_lab_sample_id"]
            # sequencing_sample_id=data["sequencing_sample_id"],
            # biosample_accession_ENA=data["biosample_accession_ENA"],
            # virus_name=data["virus_name"],
            # gisaid_id=data["gisaid_id"],
            # sequencing_date=data["sequencing_date"],
            metadata_file=metadata_file,
            state=state,
            user=user,
        )
        return new_sample


class Sample(models.Model):
    state = models.ForeignKey(SampleState, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    metadata_file = models.ForeignKey(
        Document, on_delete=models.CASCADE, null=True, blank=True
    )
    collecting_lab_sample_id = models.CharField(max_length=80)
    sequencing_sample_id = models.CharField(max_length=80)
    biosample_accession_ENA = models.CharField(max_length=80, null=True, blank=True)
    virus_name = models.CharField(max_length=80, null=True, blank=True)
    gisaid_id = models.CharField(max_length=80, null=True, blank=True)
    sequencing_date = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    # analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)

    class Meta:
        db_table = "Sample"

    def __str__(self):
        return "%s" % (self.collecting_lab_sample_id)

    def get_collecting_lab_sample_id(self):
        return "%s" % (self.collecting_lab_sample_id)

    def get_sequencing_sample_id(self):
        return "%s" % (self.sequencing_sample_id)

    def get_biosample_accession_ENA(self):
        return "%s" % (self.biosample_accession_ENA)

    def get_virus_name(self):
        return "%s" % (self.virus_name)

    def get_gisaid_id(self):
        return "%s" % (self.gisaid_id)

    def get_sequencing_date(self):
        return "%s" % (self.sequencing_date)

    def get_state(self):
        return "%s" % (self.state)

    def get_user(self):
        return "%s" % (self.user)

    def get_metadata_file(self):
        return "%s" % (self.metadata_file)

    objects = SampleManager()


# Position table
class PositionManager(models.Manager):
    def create_new_position(self, data):
        new_position = self.create(
            pos=data["pos"],
            nucleotide=data["nucleotide"],
        )
        return new_position


class Position(models.Model):
    pos = models.CharField(max_length=100)
    nucleotide = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Position"

    def __str__(self):
        return "%s" % (self.pos)

    def get_pos(self):
        return "%s" % (self.pos)

    def get_nucleotide(self):
        return "%s" % (self.nucleotide)

    objects = PositionManager()


# VariantInSample Table
class VariantInSampleManager(models.Manager):
    """
    fields => SAMPLE(0), CHROM(1), POS(2), REF(3), ALT(4),
    FILTER(5), DP(6),  REF_DP(7), ALT_DP(8), AF(9), GENE(10),
    EFFECT(11), HGVS_C(12), HGVS_P(13), HGVS_P1LETTER(14),
    CALLER(15), LINEAGE(16)
    """

    def create_new_variant_in_sample(self, data):
        new_variant_in_sample = self.create(
            dp=data["dp"],
            alt_dp=data["alt_dp"],
            ref_dp=data["ref_dp"],
            af=data["af"],
        )
        return new_variant_in_sample


class VariantInSample(models.Model):  # include Foreign Keys
    dp = models.CharField(max_length=10)
    alt_dp = models.CharField(max_length=5)
    ref_dp = models.CharField(max_length=10)
    af = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "VariantInSample"

    def get_dp(self):
        return "%s" % (self.dp)

    def get_alt_dp(self):
        return "%s" % (self.alt_dp)

    def get_ref_dp(self):
        return "%s" % (self.ref_dp)

    def get_af(self):
        return "%s" % (self.af)

    objects = VariantInSampleManager()


# Variant Table
class VariantManager(models.Manager):
    def create_new_variant(self, data, data_ids):
        new_variant = self.create(
            ref=data,
            sampleID_id=data_ids["sampleID_id"],
            variant_in_sampleID_id=data_ids["variant_in_sampleID_id"],
            filterID_id=data_ids["filterID_id"],
            positionID_id=data_ids["positionID_id"],
            chromosomeID_id=data_ids["chromosomeID_id"],
            geneID_id=data_ids["geneID_id"],
            effectID_id=data_ids["effectID_id"],
        )
        return new_variant


class Variant(models.Model):
    sampleID_id = models.ForeignKey(Sample, on_delete=models.CASCADE)
    variant_in_sampleID_id = models.ForeignKey(
        VariantInSample, on_delete=models.CASCADE
    )
    filterID_id = models.ForeignKey(Filter, on_delete=models.CASCADE)
    positionID_id = models.ForeignKey(Position, on_delete=models.CASCADE)
    chromosomeID_id = models.ForeignKey(Chromosome, on_delete=models.CASCADE)
    geneID_id = models.ForeignKey(Gene, on_delete=models.CASCADE)
    effectID_id = models.ForeignKey(Effect, on_delete=models.CASCADE)

    ref = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Variant"

    def get_ref(self):
        return "%s" % (self.ref)

    objects = VariantManager()


# Table Analysis
class AnalysisManager(models.Manager):
    def create_new_analysis(self, data):
        new_analysis = self.create(
            raw_sequence_data_processing_method=data[
                "raw_sequence_data_processing_method"
            ],
            dehosting_method=data["dehosting_method"],
            assembly=data["assembly"],
            if_assembly_other=data["if_assembly_other"],
            assembly_params=data["assembly_params"],
            variant_calling=data["variant_calling"],
            if_variant_calling_other=data["if_variant_calling_other"],
            variant_calling_params=data["variant_calling_params"],
            consensus_sequence_name=data["consensus_sequence_name"],
            consensus_sequence_name_md5=data["consensus_sequence_name_md5"],
            consensus_sequence_filepath=data["consensus_sequence_filepath"],
            consensus_sequence_software_name=data["consensus_sequence_software_name"],
            if_consensus_other=data["if_consensus_other"],
            consensus_sequence_software_version=data[
                "consensus_sequence_software_version"
            ],
            consensus_criteria=data["consensus_criteria"],
            reference_genome_accession=data["reference_genome_accession"],
            bioinformatics_protocol=data["bioinformatics_protocol"],
            if_bioinformatic_protocol_is_other_specify=data[
                "if_bioinformatic_protocol_is_other_specify"
            ],
            bioinformatic_protocol_version=data["bioinformatic_protocol_version"],
            analysis_date=data["analysis_date"],
            commercial_open_source_both=data["commercial_open_source_both"],
            preprocessing=data["preprocessing"],
            if_preprocessing_other=data["if_preprocessing_other"],
            preprocessing_params=data["preprocessing_params"],
            mapping=data["mapping"],
            if_mapping_other=data["if_mapping_other"],
            mapping_params=data["mapping_params"],
        )
        return new_analysis


class Analysis(models.Model):
    raw_sequence_data_processing_method = models.CharField(max_length=100)
    dehosting_method = models.CharField(max_length=100)
    assembly = models.CharField(max_length=100)
    if_assembly_other = models.CharField(max_length=100)
    assembly_params = models.CharField(max_length=100)
    variant_calling = models.CharField(max_length=100)
    if_variant_calling_other = models.CharField(max_length=100)
    variant_calling_params = models.CharField(max_length=100)
    consensus_sequence_name = models.CharField(max_length=100)
    consensus_sequence_name_md5 = models.CharField(max_length=100)
    consensus_sequence_filepath = models.CharField(max_length=100)
    consensus_sequence_software_name = models.CharField(max_length=100)
    if_consensus_other = models.CharField(max_length=100)
    consensus_sequence_software_version = models.CharField(max_length=100)
    consensus_criteria = models.CharField(max_length=100)
    reference_genome_accession = models.CharField(max_length=100)
    bioinformatics_protocol = models.CharField(max_length=100)
    if_bioinformatic_protocol_is_other_specify = models.CharField(max_length=100)
    bioinformatic_protocol_version = models.CharField(max_length=100)
    analysis_date = models.CharField(max_length=100)
    commercial_open_source_both = models.CharField(max_length=100)
    preprocessing = models.CharField(max_length=100)
    if_preprocessing_other = models.CharField(max_length=100)
    preprocessing_params = models.CharField(max_length=100)
    mapping = models.CharField(max_length=100)
    if_mapping_other = models.CharField(max_length=100)
    mapping_params = models.CharField(max_length=100)
    reference_genome_accession = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    # Many-to-one relationships
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)

    class Meta:
        db_table = "Analysis"

    def __str__(self):
        return "%s" % (self.raw_sequence_data_processing_method)

    def get_raw_sequence_data_processing_method(self):
        return "%s" % (self.raw_sequence_data_processing_method)

    def get_dehosting_method(self):
        return "%s" % (self.dehosting_method)

    def get_assembly(self):
        return "%s" % (self.assembly)

    def get_if_assembly_other(self):
        return "%s" % (self.if_assembly_other)

    def get_assembly_params(self):
        return "%s" % (self.assembly_params)

    def get_variant_calling(self):
        return "%s" % (self.variant_calling)

    def get_if_variant_calling_other(self):
        return "%s" % (self.if_variant_calling_other)

    def get_variant_calling_params(self):
        return "%s" % (self.variant_calling_params)

    def get_consensus_sequence_name(self):
        return "%s" % (self.consensus_sequence_name)

    def get_consensus_sequence_name_md5(self):
        return "%s" % (self.consensus_sequence_name_md5)

    def get_consensus_sequence_filepath(self):
        return "%s" % (self.consensus_sequence_filepath)

    def get_consensus_sequence_software_name(self):
        return "%s" % (self.consensus_sequence_software_name)

    def get_if_consensus_other(self):
        return "%s" % (self.if_consensus_other)

    def get_consensus_sequence_software_version(self):
        return "%s" % (self.consensus_sequence_software_version)

    def get_consensus_criteria(self):
        return "%s" % (self.consensus_criteria)

    def get_bioinformatics_protocol(self):
        return "%s" % (self.bioinformatics_protocol)

    def get_if_bioinformatic_protocol_is_other_specify(self):
        return "%s" % (self.if_bioinformatic_protocol_is_other_specify)

    def get_bioinformatic_protocol_version(self):
        return "%s" % (self.bioinformatic_protocol_version)

    def get_analysis_date(self):
        return "%s" % (self.analysis_date)

    def get_commercial_open_source_both(self):
        return "%s" % (self.commercial_open_source_both)

    def get_preprocessing(self):
        return "%s" % (self.preprocessing)

    def get_if_preprocessing_other(self):
        return "%s" % (self.if_preprocessing_other)

    def get_preprocessing_params(self):
        return "%s" % (self.preprocessing_params)

    def get_mapping(self):
        return "%s" % (self.mapping)

    def get_if_mapping_other(self):
        return "%s" % (self.if_mapping_other)

    def get_mapping_params(self):
        return "%s" % (self.mapping_params)

    def get_reference_genome_accession(self):
        return "%s" % (self.reference_genome_accession)

    objects = AnalysisManager()


# table Authors
class AuthorsManager(models.Manager):
    def create_new_authors(self, data):
        analysis_authors = ""
        author_submitter = ""
        new_authors = self.create(
            analysis_authors=analysis_authors,
            author_submitter=author_submitter,
            # analysis_authors=data["analysis_authors"],
            # author_submitter=data["author_submitter"],
            authors=data["authors"],
        )
        return new_authors


class Authors(models.Model):
    analysis_authors = models.CharField(max_length=100)
    author_submitter = models.CharField(max_length=100)
    authors = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Authors"

    def __str__(self):
        return "%s" % (self.analysis_authors)

    def get_analysis_author(self):
        return "%s" % (self.analysis_authors)

    def get_author_submitter(self):
        return "%s" % (self.author_submitter)

    def get_authors(self):
        return "%s" % (self.authors)

    objects = AuthorsManager()


# table QcStats
class QcStatsManager(models.Manager):
    def create_new_qc_stats(self, data):
        new_qc_stats = self.create(
            quality_control_metrics=data["quality_control_metrics"],
            breadth_of_coverage_value=data["breadth_of_coverage_value"],
            depth_of_coverage_value=data["depth_of_coverage_value"],
            depth_of_coverage_threshold=data["depth_of_coverage_threshold"],
            number_of_base_pairs_sequenced=data["number_of_base_pairs_sequenced"],
            consensus_genome_length=data["consensus_genome_length"],
            ns_per_100_kbp=data["ns_per_100_kbp"],
            per_qc_filtered=data["per_qc_filtered"],
            per_reads_host=data["per_reads_host"],
            per_reads_virus=data["per_reads_virus"],
            per_unmapped=data["per_unmapped"],
            per_genome_greater_10x=data["per_genome_greater_10x"],
            mean_depth_of_coverage_value=data["mean_depth_of_coverage_value"],
            per_Ns=data["per_Ns"],
            number_of_variants_AF_greater_75percent=data[
                "number_of_variants_AF_greater_75percent"
            ],
            number_of_variants_with_effect=data["number_of_variants_with_effect"],
        )
        return new_qc_stats


class QcStats(models.Model):
    quality_control_metrics = models.CharField(max_length=100)
    breadth_of_coverage_value = models.CharField(max_length=100)
    depth_of_coverage_value = models.CharField(max_length=100)
    depth_of_coverage_threshold = models.CharField(max_length=100)
    number_of_base_pairs_sequenced = models.CharField(max_length=100)
    consensus_genome_length = models.CharField(max_length=100)
    ns_per_100_kbp = models.CharField(max_length=100)
    per_qc_filtered = models.CharField(max_length=100)
    per_reads_host = models.CharField(max_length=100)
    per_reads_virus = models.CharField(max_length=100)
    per_unmapped = models.CharField(max_length=100)
    per_genome_greater_10x = models.CharField(max_length=100)
    mean_depth_of_coverage_value = models.CharField(max_length=100)
    per_Ns = models.CharField(max_length=100)
    number_of_variants_AF_greater_75percent = models.CharField(max_length=100)
    number_of_variants_with_effect = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    # One-to-one relationships
    analysis = models.OneToOneField(
        Analysis, on_delete=models.CASCADE, primary_key=True
    )

    class Meta:
        db_table = "QCStats"

    def __str__(self):
        return "%s" % (self.quality_control_metrics)

    def get_quality_control_metrics(self):
        return "%s" % (self.quality_control_metrics)

    def get_breadth_of_coverage_value(self):
        return "%s" % (self.breadth_of_coverage_value)

    def get_depth_of_coverage_value(self):
        return "%s" % (self.depth_of_coverage_value)

    def get_depth_of_coverage_threshold(self):
        return "%s" % (self.depth_of_coverage_threshold)

    def get_number_of_base_pairs_sequenced(self):
        return "%s" % (self.number_of_base_pairs_sequenced)

    def get_consensus_genome_length(self):
        return "%s" % (self.consensus_genome_length)

    def get_ns_per_100_kbp(self):
        return "%s" % (self.ns_per_100_kbp)

    def get_per_qc_filtered(self):
        return "%s" % (self.per_qc_filtered)

    def get_per_reads_host(self):
        return "%s" % (self.per_reads_host)

    def get_per_reads_virus(self):
        return "%s" % (self.per_reads_virus)

    def get_per_unmapped(self):
        return "%s" % (self.per_unmapped)

    def get_per_genome_greater_10x(self):
        return "%s" % (self.per_genome_greater_10x)

    def get_mean_depth_of_coverage_value(self):
        return "%s" % (self.mean_depth_of_coverage_value)

    def get_per_Ns(self):
        return "%s" % (self.per_Ns)

    def get_Number_of_variants_AF_greater_75percent(self):
        return "%s" % (self.Number_of_variants_AF_greater_75percent)

    def get_Numer_of_variants_with_effect(self):
        return "%s" % (self.Numer_of_variants_with_effect)

    objects = QcStatsManager()


# table PublicDatabase
class PublicDatabaseManager(models.Manager):
    def create_new_public_database(self, data):
        new_public_database = self.create(databaseName=data["databaseName"])
        return new_public_database


class PublicDatabase(models.Model):
    databaseName = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    # ManyToOne
    authors = models.ForeignKey(Authors, on_delete=models.CASCADE)

    class Meta:
        db_table = "PublicDatabase"

    def __str__(self):
        return "%s" % (self.databaseName)

    objects = PublicDatabaseManager()


# table PublicDatabaseField
class PublicDatabaseFieldManager(models.Manager):
    def create_new_public_database_field(self, data):
        new_public_database_field = self.create(
            fieldName=data["fieldName"],
            fieldDescription=data["fieldDescription"],
            fieldInUse=data["fieldInUse"],
        )
        return new_public_database_field


class PublicDatabaseField(models.Model):
    publicDatabaseID = models.ForeignKey(
        PublicDatabase, on_delete=models.CASCADE, null=True, blank=True
    )
    fieldName = models.CharField(max_length=50)
    fieldDescription = models.CharField(max_length=400, null=True, blank=True)
    fieldInUse = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    # ManyToOne
    # public_database = models.ForeignKey(PublicDatabase, on_delete= models.CASCADE)

    class Meta:
        db_table = "PublicDatabaseField"

    def __str__(self):
        return "%s" % (self.fieldName)

    def get_public_database_id(self):
        return "%s" % (self.publicDatabaseID)

    def get_field_name(self):
        return "%s" % (self.fieldName)

    def get_field_description(self):
        return "%s" % (self.fieldDescription)

    def get_field_in_use(self):
        return "%s" % (self.fieldInUse)

    objects = PublicDatabaseFieldManager()


class TemporalSampleStorageManager(models.Manager):
    def save_temp_data(self, data):
        new_t_data = self.create(
            sample_idx=data["sample_idx"],
            field=data["field"],
            value=data["value"]
        )
        return new_t_data


class TemporalSampleStorage(models.Model):
    sample_idx = models.IntegerField()
    field = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    sent = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "%s,%s" % (self.sample, self.field)

    def get_temp_values(self):
        return {self.field: self.value}

    def update_sent_status(self, value):
        self.sent = value
        self.save()
        return

    objects = TemporalSampleStorageManager()


class ConfigSettingManager(models.Manager):
    def create_config_setting(self, configuration_name, configuration_value):
        new_config_settings = self.create(
            configurationName=configuration_name, configurationValue=configuration_value
        )
        return new_config_settings


class ConfigSetting(models.Model):
    configuration_name = models.CharField(max_length=80)
    configuration_value = models.CharField(max_length=255, null=True, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ConfigSetting"

    def __str__(self):
        return "%s" % (self.configuration_name)

    def get_configuration_value(self):
        return "%s" % (self.configuration_value)

    def set_configuration_value(self, new_value):
        self.configuration_value = new_value
        self.save()
        return self

    objects = ConfigSettingManager()
