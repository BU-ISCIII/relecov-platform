from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from relecov_core.core_config import SCHEMAS_UPLOAD_FOLDER


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


class BioinfoMetadataFile(models.Model):
    title = models.CharField(max_length=200)
    file_path = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "BioinfoMetadataFile"

    def __str__(self):
        return "%s" % (self.title)

    def get_title(self):
        return "%s" % (self.title)

    def get_file_path(self):
        return "%s" % (self.file_path)

    def get_uploaded_file(self):
        return "%s" % (self.uploadedFile)


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


class ClassificationManager(models.Manager):
    def create_new_classification(self, classification_name):
        new_class_obj = self.create(classification_name=classification_name)
        return new_class_obj


class Classification(models.Model):
    classification_name = models.CharField(max_length=100)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = "Classification"

    def __str__(self):
        return "%s" % (self.classification_name)

    def get_classification_id(self):
        return "%s" % (self.pk)

    def get_classification_name(self):
        return "%s" % (self.classification_name)

    objects = ClassificationManager()


class SchemaPropertiesManager(models.Manager):
    def create_new_property(self, data):
        required = True if "required" in data else False
        options = True if "options" in data else False
        format = data["format"] if "format" in data else None
        if Classification.objects.filter(
            classification_name__iexact=data["classification"]
        ).exists():
            classification_id = Classification.objects.filter(
                classification_name=data["classification"]
            ).last()
        else:
            classification_id = Classification.objects.create_new_classification(
                data["classification"]
            )

        new_property_obj = self.create(
            schemaID=data["schemaID"],
            property=data["property"],
            examples=data["examples"],
            ontology=data["ontology"],
            type=data["type"],
            description=data["description"],
            label=data["label"],
            classificationID=classification_id,
            fill_mode=data["fill_mode"],
            required=required,
            options=options,
            format=format,
        )
        return new_property_obj


class SchemaProperties(models.Model):
    schemaID = models.ForeignKey(Schema, on_delete=models.CASCADE)
    classificationID = models.ForeignKey(
        Classification, on_delete=models.CASCADE, null=True, blank=True
    )
    property = models.CharField(max_length=50)
    examples = models.CharField(max_length=200, null=True, blank=True)
    ontology = models.CharField(max_length=40, null=True, blank=True)
    type = models.CharField(max_length=20)
    format = models.CharField(max_length=20, null=True, blank=True)
    description = models.CharField(max_length=250, null=True, blank=True)
    label = models.CharField(max_length=200, null=True, blank=True)
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
        if self.classificationID:
            classification = self.classificationID.get_classification_name()
        else:
            classification = ""
        data = []
        data.append(self.property)
        data.append(self.label)
        data.append(self.required)
        data.append(classification)
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

    def get_fill_mode(self):
        return "%s" % (self.fill_mode)

    def get_classification(self):
        if self.classificationID is not None:
            return self.classificationID.get_classification_name()
        return ""

    objects = SchemaPropertiesManager()


class PropertyOptionsManager(models.Manager):
    def create_property_options(self, data):
        new_property_option_obj = self.create(
            propertyID=data["propertyID"],
            enum=data["enum"],
            ontology=data["ontology"],
        )
        return new_property_option_obj


class PropertyOptions(models.Model):
    propertyID = models.ForeignKey(SchemaProperties, on_delete=models.CASCADE)
    enum = models.CharField(max_length=80, null=True, blank=True)
    ontology = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        db_table = "PropertyOptions"

    def __str__(self):
        return "%s" % (self.enum)

    def get_enum(self):
        return "%s" % (self.enum)

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


class BioinfoAnalysisFieldManager(models.Manager):
    def create_new_field(self, data):
        new_field = self.create(
            property_name=data["property_name"],
            label_name=data["label_name"],
        )
        return new_field


class BioinfoAnalysisField(models.Model):
    schemaID = models.ManyToManyField(Schema)
    property_name = models.CharField(max_length=60)
    label_name = models.CharField(max_length=80)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = "BioinfoAnalysisField"

    def __str__(self):
        return "%s" % (self.property_name)

    def get_id(self):
        return "%s" % (self.pk)

    def get_property(self):
        return "%s" % (self.property_name)

    def get_label(self):
        return "%s" % (self.label_name)

    def get_classification_name(self):
        if self.classificationID is not None:
            return self.classificationID.get_classification()
        return None

    objects = BioinfoAnalysisFieldManager()


class BioInfoAnalysisValueManager(models.Manager):
    def create_new_value(self, data):
        new_value = self.create(
            value=data["value"],
            bioinfo_analysis_fieldID=data["bioinfo_analysis_fieldID"],
            sampleID_id=data["sampleID_id"],
        )
        return new_value


class BioInfoAnalysisValue(models.Model):
    value = models.CharField(max_length=240)
    bioinfo_analysis_fieldID = models.ForeignKey(
        BioinfoAnalysisField, on_delete=models.CASCADE
    )
    # sampleID_id = models.ForeignKey(Sample, on_delete=models.CASCADE)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = "BioInfoAnalysisValue"

    def __str__(self):
        return "%s" % (self.value)

    def get_value(self):
        return "%s" % (self.value)

    def get_id(self):
        return "%s" % (self.pk)

    def get_b_process_field_id(self):
        return "%s" % (self.bioinfo_analysis_fieldID)


class LineageInfo(models.Model):
    lineage_name = models.CharField(max_length=100)
    pango_lineages = models.CharField(max_length=100)
    variant_name = models.CharField(max_length=100)
    nextclade = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "LineageInfo"

    def __str__(self):
        return "%s" % (self.lineage_name)

    def get_lineage_name(self):
        return "%s" % (self.lineage_name)

    def get_lineage_id(self):
        return "%s" % (self.pk)


class LineageFieldsManager(models.Manager):
    def create_new_field(self, data):
        new_field = self.create(
            property_name=data["property_name"],
            label_name=data["label_name"],
        )
        return new_field


class LineageFields(models.Model):
    schemaID = models.ManyToManyField(Schema)
    property_name = models.CharField(max_length=60)
    label_name = models.CharField(max_length=80)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = "LineageFields"

    def __str__(self):
        return "%s" % (self.property_name)

    def get_lineage_property_name(self):
        return "%s" % (self.property_name)

    def get_lineage_field_id(self):
        return "%s" % (self.pk)

    objects = LineageFieldsManager()


class LineageValues(models.Model):
    # sampleID_id = models.ForeignKey(Sample, on_delete=models.CASCADE)
    lineage_fieldID = models.ForeignKey(LineageFields, on_delete=models.CASCADE)
    value = models.CharField(max_length=240)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = "LinageValue"

    def __str__(self):
        return "%s" % (self.value)

    def get_value(self):
        return "%s" % (self.value)

    def get_id(self):
        return "%s" % (self.pk)

    def get_lineage_field(self):
        return "%s" % (self.lineage_fieldID)


class OrganismAnnotationManger(models.Manager):
    def create_new_annotation(self, data):
        new_annotation = self.create(
            user=data["user"],
            gff_version=data["gff_version"],
            gff_spec_version=data["gff_spec_version"],
            sequence_region=data["sequence_region"],
            organism_code=data["organism_code"],
            organism_code_version=data["organism_code_version"],
        )
        return new_annotation


class OrganismAnnotation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    gff_version = models.CharField(max_length=5)
    gff_spec_version = models.CharField(max_length=10)
    sequence_region = models.CharField(max_length=30)
    organism_code = models.CharField(max_length=20)
    organism_code_version = models.CharField(max_length=10)

    class Meta:
        db_table = "OrganismAnnotation"

    def __str__(self):
        return "%s" % (self.organism_code)

    def get_organism_code(self):
        return "%s" % (self.organism_code)

    def get_organism_code_version(self):
        return "%s" % (self.organism_code_version)

    def get_full_information(self):
        data = []
        data.append(self.pk)
        data.append(self.organism_code)
        data.append(self.organism_code_version)
        data.append(self.gff_spec_version)
        data.append(self.sequence_region)
        return data

    objects = OrganismAnnotationManger()


class Filter(models.Model):
    filter = models.CharField(max_length=70)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Filter"

    def __str__(self):
        return "%s" % (self.filter)

    def get_filter(self):
        return "%s" % (self.filter)

    def get_filter_id(self):
        return "%s" % (self.pk)


class Effect(models.Model):
    effect = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "Effect"

    def __str__(self):
        return "%s" % (self.effect)

    def get_effect_id(self):
        return "%s" % (self.pk)

    def get_effect(self):
        return "%s" % (self.effect)


# Gene Table
class GeneManager(models.Manager):
    def create_new_gene(self, data):
        new_gene = self.create(
            gene_name=data["gene_name"],
            gene_start=data["gene_start"],
            gene_end=data["gene_end"],
            user=data["user"],
            org_annotationID=data["org_annotationID"],
        )
        return new_gene


class Gene(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    org_annotationID = models.ForeignKey(
        OrganismAnnotation, on_delete=models.CASCADE, null=True, blank=True
    )
    gene_name = models.CharField(max_length=50)
    gene_start = models.IntegerField()
    gene_end = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Gene"

    def __str__(self):
        return "%s" % (self.gene_name)

    def get_gene_name(self):
        return "%s" % (self.gene_name)

    def get_gene_id(self):
        return "%s" % (self.pk)

    def get_gene_positions(self):
        return [str(self.gene_start), str(self.gene_end)]

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

    def get_chromosome_name(self):
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
        return "%s" % (self.state)

    def get_state_id(self):
        return "%s" % (self.pk)

    def get_state_display_string(self):
        return "%s" % (self.display_string)


class Error(models.Model):
    error_name = models.CharField(max_length=100)
    display_string = models.CharField(max_length=100)
    description = models.CharField(max_length=100)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = "Error"

    def __str__(self):
        return "%s" % (self.error_name)

    def get_error_name(self):
        return "%s" % (self.error_name)

    def get_error_id(self):
        return "%s" % (self.pk)

    def get_display_string(self):
        return "%s" % (self.display_string)

    def get_description(self):
        return "%s" % (self.description)


# Sample Table
class SampleManager(models.Manager):
    def create_new_sample(self, data):
        state = SampleState.objects.filter(state__exact=data["state"]).last()
        new_sample = self.create(
            sample_unique_id=data["sample_unique_id"],
            sequencing_sample_id=data["sequencing_sample_id"],
            sequencing_date=data["sequencing_date"],
            metadata_file=data["metadata_file"],
            state=state,
            user=data["user"],
        )
        return new_sample


class Sample(models.Model):
    state = models.ForeignKey(SampleState, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    error_type = models.ForeignKey(
        Error, on_delete=models.CASCADE, null=True, blank=True
    )
    schema_obj = models.ForeignKey(
        Schema, on_delete=models.CASCADE, null=True, blank=True
    )
    linage_values = models.ManyToManyField(LineageValues, blank=True)
    linage_info = models.ManyToManyField(LineageInfo, blank=True)
    bio_analysis_values = models.ManyToManyField(BioInfoAnalysisValue, blank=True)

    sample_unique_id = models.CharField(max_length=12)
    microbiology_lab_sample_id = models.CharField(max_length=80, null=True, blank=True)
    collecting_lab_sample_id = models.CharField(max_length=80, null=True, blank=True)
    sequencing_sample_id = models.CharField(max_length=80, null=True, blank=True)
    submitting_lab_sample_id = models.CharField(max_length=80, null=True, blank=True)
    sequence_file_R1_fastq = models.CharField(max_length=80, null=True, blank=True)
    sequence_file_R2_fastq = models.CharField(max_length=80, null=True, blank=True)
    fastq_r1_md5 = models.CharField(max_length=80, null=True, blank=True)
    fastq_r2_md5 = models.CharField(max_length=80, null=True, blank=True)
    r1_fastq_filepath = models.CharField(max_length=120, null=True, blank=True)
    r2_fastq_filepath = models.CharField(max_length=120, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Sample"

    def __str__(self):
        return "%s" % (self.sequencing_sample_id)

    def get_lineage_values(self):
        return "%s" % (self.linage_values)

    def get_sample_id(self):
        return "%s" % (self.pk)

    def get_sequencing_sample_id(self):
        return "%s" % (self.sequencing_sample_id)

    def get_collecting_lab_sample_id(self):
        return "%s" % (self.collecting_lab_sample_id)

    def get_unique_id(self):
        return "%s" % (self.sample_unique_id)

    def get_schema_obj(self):
        if self.schema_obj:
            return self.schema_obj
        return None

    def get_ena_info(self):
        if self.ena_obj is None:
            return ""
        return self.ena_obj.get_ena_data()

    def get_state(self):
        if self.state:
            return "%s" % (self.state.get_state())
        return None

    def get_user(self):
        return "%s" % (self.user)

    def get_info_for_searching(self):
        recorded_date = self.created_at.strftime("%d , %B , %Y")
        data = []
        data.append(self.pk)
        data.append(self.sequencing_sample_id)
        data.append(self.get_state())
        data.append(recorded_date)
        return data

    def get_sample_basic_data(self):
        recorded_date = self.created_at.strftime("%d , %B , %Y")
        data = []
        data.append(self.sequencing_sample_id)
        data.append(self.microbiology_lab_sample_id)
        data.append(self.submitting_lab_sample_id)
        data.append(self.get_state())
        data.append(recorded_date)
        return data

    def get_fastq_data(self):
        data = []
        data.append(self.sequence_file_R1_fastq)
        data.append(self.sequence_file_R2_fastq)
        data.append(self.r1_fastq_filepath)
        data.append(self.r2_fastq_filepath)
        data.append(self.fastq_r1_md5)
        data.append(self.fastq_r2_md5)
        return data

    def update_state(self, state):
        if not SampleState.objects.filter(state__exact=state).exists():
            return False
        self.state = SampleState.objects.filter(state__exact=state).last()
        self.save()
        return self

    objects = SampleManager()


class PublicDatabaseType(models.Model):
    public_type_name = models.CharField(max_length=30)
    public_type_display = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "PublicDatabaseType"

    def __str__(self):
        return "%s" % (self.public_type_name)

    def get_public_type_name(self):
        return "%s" % (self.public_type_name)

    def get_public_type_display(self):
        return "%s" % (self.public_type_display)


class PublicDatabaseFieldsManager(models.Manager):
    def create_new_field(self, data):
        new_field = self.create(
            database_type=data["database_type"],
            property_name=data["property_name"],
            label_name=data["label_name"],
        )
        return new_field


class PublicDatabaseFields(models.Model):
    schemaID = models.ManyToManyField(Schema)
    database_type = models.ForeignKey(
        PublicDatabaseType, on_delete=models.CASCADE, null=True, blank=True
    )
    property_name = models.CharField(max_length=60)
    label_name = models.CharField(max_length=80)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "PublicDatabaseFields"

    def __str__(self):
        return "%s" % (self.property_name)

    def get_property_name(self):
        return "%s" % (self.property_name)

    def get_label_name(self):
        return "%s" % (self.label_name)

    objects = PublicDatabaseFieldsManager()


class PublicDatabaseValues(models.Model):
    public_database_fieldID = models.ForeignKey(
        PublicDatabaseFields, on_delete=models.CASCADE
    )
    sampleID = models.ForeignKey(
        Sample, on_delete=models.CASCADE, null=True, blank=True
    )
    value = models.CharField(max_length=240)
    generated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = "PublicDatabaseValues"

    def __str__(self):
        return "%s" % (self.value)

    def get_value(self):
        return "%s" % (self.value)

    def get_id(self):
        return "%s" % (self.pk)


class DateUpdateState(models.Model):
    stateID = models.ForeignKey(SampleState, on_delete=models.CASCADE)
    sampleID = models.ForeignKey(Sample, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "DateUpdateState"

    def __str__(self):
        return "%s_%s" % (self.stateID, self.sampleID)

    def get_state_name(self):
        if self.stateID is not None:
            return "%s" % (self.stateID.get_state_display_string())

    def get_date(self):
        return self.date.strftime("%B %d, %Y")


# CHROM	POS	REF	ALT
class Variant(models.Model):
    chromosomeID_id = models.ForeignKey(
        Chromosome, on_delete=models.CASCADE, null=True, blank=True
    )
    filterID_id = models.ForeignKey(
        Filter, on_delete=models.CASCADE, null=True, blank=True
    )
    ref = models.CharField(max_length=60, null=True, blank=True)
    pos = models.CharField(max_length=60, null=True, blank=True)
    alt = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "Variant"

    def __str__(self):
        return "%s_%s" % (self.pos, self.alt)

    def get_variant_id(self):
        return "%s" % (self.pk)

    def get_ref(self):
        return "%s" % (self.ref)

    def get_pos(self):
        return "%s" % (self.pos)

    def get_chrom(self):
        return "%s" % (self.chrom)

    def get_alt(self):
        return "%s" % (self.alt)


# FILTER	DP	REF_DP	ALT_DP	AF
class VariantInSample(models.Model):  # include Foreign Keys
    sampleID_id = models.ForeignKey(
        Sample, on_delete=models.CASCADE, null=True, blank=True
    )
    variantID_id = models.ForeignKey(
        Variant, on_delete=models.CASCADE, null=True, blank=True
    )
    dp = models.CharField(max_length=10, null=True, blank=True)
    ref_dp = models.CharField(max_length=10, null=True, blank=True)
    alt_dp = models.CharField(max_length=5, null=True, blank=True)
    af = models.CharField(max_length=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))

    class Meta:
        db_table = "VariantInSample"

    def __str__(self):
        return "%s" % (self.dp)

    def get_variant_in_sample_id(self):
        return "%s" % (self.pk)

    def get_variantID_id(self):
        return "%s" % (self.variantID_id.get_variant_id())

    def get_dp(self):
        return "%s" % (self.dp)

    def get_ref_dp(self):
        return "%s" % (self.ref_dp)

    def get_alt_dp(self):
        return "%s" % (self.alt_dp)

    def get_af(self):
        return "%s" % (self.af)

    def get_variant_pos(self):
        return self.variantID_id.get_pos()

    def get_variant_in_sample_data(self):
        data = []
        data.append(self.dp)
        data.append(self.ref_dp)
        data.append(self.alt_dp)
        data.append(self.af)
        return data


# variant annotation GENE	EFFECT??	HGVS_C	HGVS_P	HGVS_P_1LETTER
class VariantAnnotation(models.Model):
    geneID_id = models.ForeignKey(Gene, on_delete=models.CASCADE)
    effectID_id = models.ForeignKey(
        Effect, on_delete=models.CASCADE, null=True, blank=True
    )
    variantID_id = models.ForeignKey(
        Variant, on_delete=models.CASCADE, null=True, blank=True
    )
    hgvs_c = models.CharField(max_length=60)
    hgvs_p = models.CharField(max_length=60)
    hgvs_p_1_letter = models.CharField(max_length=100)

    class Meta:
        db_table = "VariantAnnotation"

    def __str__(self):
        return "%s" % (self.variantID_id)

    def get_variant_annotation_id(self):
        return "%s" % (self.pk)

    def get_geneID_id(self):
        return "%s" % (self.geneID_id)

    def get_effectID_id(self):
        return "%s" % (self.effectID_id)

    def get_variant_in_sample_data(self):
        data = []
        data.append(self.hgvs_c)
        data.append(self.hgvs_p)
        data.append(self.hgvs_p_1_letter)
        return data


class TemporalSampleStorageManager(models.Manager):
    def save_temp_data(self, data):
        new_t_data = self.create(
            sample_idx=data["sample_idx"], field=data["field"], value=data["value"]
        )
        return new_t_data


class TemporalSampleStorage(models.Model):
    sample_idx = models.IntegerField()
    field = models.CharField(max_length=100)
    value = models.CharField(max_length=100)
    sent = models.BooleanField(default=False)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "TemporalSampleStorage"

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
