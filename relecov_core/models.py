#from webbrowser import Chrome
from django.db import models
from django.forms import CharField

# Caller Table
class CallerManager(models.Manager):
    def create_new_caller(self, data):
        new_caller = self.create(name=data["name"], version=data["version"])
        return new_caller


class Caller(models.Model):
    name = models.CharField(max_length=60)
    version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))

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
        new_filter = self.create(filter=data["filter"])
        return new_filter


class Filter(models.Model):
    filter = models.CharField(max_length=70)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))

    class Meta:
        db_table = "Filter"

    def __str__(self):
        return "%s" % (self.filter)

    objects = FilterManager()


# Effect Table
class EffectManager(models.Manager):
    def create_new_effect(self, data):
        new_effect = self.create(
            effect=data["effect"],
            hgvs_c=data["hgvs_c"],
            hgvs_p=data["hgvs_p"],
            hgvs_p_1_letter=data["hgvs_p_1_letter"],
        )
        return new_effect


class Effect(models.Model):
    effect = models.CharField(max_length=80)
    hgvs_c = models.CharField(max_length=60)
    hgvs_p = models.CharField(max_length=60)
    hgvs_p_1_letter = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))

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
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))

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
        new_gene = self.create(gene=data["gene"])
        return new_gene


class Gene(models.Model):
    gene = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))

    class Meta:
        db_table = "Gene"

    def __str__(self):
        return "%s" % (self.gene)

    objects = GeneManager()


# Chromosome Table
class ChromosomeManager(models.Manager):
    def create_new_chromosome(self, data):
        new_chomosome = self.create(chromosome=data["chromosome"])
        return new_chomosome


class Chromosome(models.Model):
    chromosome = models.CharField(max_length=110)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))

    class Meta:
        db_table = "Chromosome"

    def __str__(self):
        return "%s" % (self.chromosome)

    objects = ChromosomeManager()


# Sample Table
class SampleManager(models.Manager):
    def create_new_sample(self, data):
        new_sample = self.create(
            collecting_lab_sample_id=data["collecting_lab_sample_id"],
            sequencing_sample_id=data["sequencing_sample_id"],
            biosample_accession_ENA=data["biosample_accession_ENA"],
            virus_name=data["virus_name"],
            gisaid_id=data["gisaid_id"],
            sequencing_date=data["sequencing_date"]
        )
        return new_sample


class Sample(models.Model):
    collecting_lab_sample_id = models.CharField(max_length=80)
    sequencing_sample_id = models.CharField(max_length=80)
    biosample_accession_ENA = models.CharField(max_length=80)
    virus_name = models.CharField(max_length=80)
    gisaid_id = models.CharField(max_length=80)
    sequencing_date = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    #Many-to-one relationships
    #analysis = models.ForeignKey(Analysis, on_delete=models.CASCADE)
    
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
    
    objects = SampleManager()


# SampleOther Table
"""
class SampleOtherManager(models.Manager):
    def create_new_sample_other(self, data):
        new_sample_other = self.create(
            collecting_lab_sample_id=data["collecting_lab_sample_id"],
            sequencing_sample_id=data["sequencing_sample_id"],
            biosample_accession_ENA=data["biosample_accession_ENA"],
            virus_name=data["virus_name"],
            gisaid_id=data["gisaid_id"],
            sequencing_date=data["sequencing_date"],
            ##########################################################
            public_health_sample_id_sivies = data["public_health_sample_id_sivies"], #Public Health sample id (SIVIES)
            submitting_lab_sample_id = data["submitting_lab_sample_id"], #Sample ID given by the submitting laboratory
            microbiology_lab_sample_id = data["microbiology_lab_sample_id"], #Sample ID given in the microbiology lab
            isolate_sample_id = data["isolate_sample_id"], #Sample ID given if multiple rna-extraction or passages
            collecting_institution = data["collecting_institution"], #Originating Laboratory
            sample_collection_date = data["sample_collection_date"],#Sample Collection Date
            sample_received_date = data["sample_received_date"], #Sample Received Date
            anatomical_material =  data["anatomical_material"], #Specimen source
            environmental_material =  data["environmental_material"], #Environmental Material
            host_age =  data["host_age"], #Host Age
            host_gender =  data["host_gender"], #Host Gender
            sequence_file_R1_fastq =  data["sequence_file_R1_fastq"], #Sequence file R1 fastq
            sequence_file_R2_fastq =  data["sequence_file_R2_fastq"], #Sequence file R2 fastq
            )
        return new_sample_other


class SampleOther(models.Model):
    ########these fields appear in relecov_core/form############
    sample_storage_conditions = models.CharField(max_length=80) #Biological Sample Storage Condition 
    collection_device = models.CharField(max_length=80) #Collection Device
    rna_extraction_Protocol = models.CharField(max_length=80) #Rna Extraction Protocol
    library_kit = models.CharField(max_length=80) #Commercial All-in-one library kit
    library_preparation_kit = models.CharField(max_length=80) #Library Preparation Kit
    
     #= models.CharField(max_length=80) #
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "SampleOther"
        
    def __str__(self):
        return "%s" % (self.collection_device)
    #######################################################################################
    def sample_storage_conditions(self):
        return "%s" % (self.sample_storage_conditions)
    
    def collection_device(self):
        return "%s" % (self.collection_device)
    
    def rna_extraction_Protocol(self):
        return "%s" % (self.rna_extraction_Protocol)
    
    def get_library_kit(self):
        return "%s" % (self.library_kit)
    
    def get_library_preparation_kit(self):
        return "%s" % (self.library_preparation_kit)
    
    #def get_(self):
    #    return "%s" % (self.)
    
    
    objects = SampleOtherManager()
"""
# Variant Table
class VariantManager(models.Manager):
    def create_new_variant(self, data):
        new_variant = self.create(
            pos=data["pos"],
            ref=data["ref"],
            alt=data["alt"],
            dp=data["dp"],
            alt_dp=data["alt_dp"],
            ref_dp=data["ref_dp"],
            af=data["af"],
        )
        return new_variant


class Variant(models.Model):  # include Foreign Keys
    pos = models.CharField(max_length=7)
    ref = models.CharField(max_length=60)
    alt = models.CharField(max_length=10)
    dp = models.CharField(max_length=10)
    alt_dp = models.CharField(max_length=5)
    ref_dp = models.CharField(max_length=10)
    af = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "Variant"

    def get_pos(self):
        return "%s" % (self.pos)

    def get_ref(self):
        return "%s" % (self.ref)

    def get_alt(self):
        return "%s" % (self.alt)

    def get_dp(self):
        return "%s" % (self.dp)

    def get_alt_dp(self):
        return "%s" % (self.alt_dp)

    def get_ref_dp(self):
        return "%s" % (self.ref_dp)

    def get_af(self):
        return "%s" % (self.af)

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
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    #Many-to-one relationships
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

    def get_reference_genome_accession(self):
        return "%s" % (self.reference_genome_accession)

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
        new_authors = self.create(
            analysis_authors=data["analysis_authors"],
            author_submitter=data["author_submitter"],
            authors=data["authors"],
        )
        return new_authors


class Authors(models.Model):
    analysis_authors = models.CharField(max_length=100)
    author_submitter = models.CharField(max_length=100)
    authors = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
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
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    #One-to-one relationships
    analysis = models.OneToOneField(Analysis, on_delete=models.CASCADE, primary_key=True)
    
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


#table PublicDatabase
class PublicDatabaseManager(models.Manager):
    def create_new_public_database(self, data):
        new_public_database = self.create(
            databaseName = data["databaseName"]
        )
        return new_public_database
    

class PublicDatabase(models.Model):
    databaseName = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    #ManyToOne
    authors = models.ForeignKey(Authors, on_delete=models.CASCADE)
    

    class Meta:
        db_table = "PublicDatabase"
        
    def __str__(self):
        return "%s" % (self.databaseName)
    
    objects = PublicDatabaseManager()
    

#table PublicDatabaseField
class PublicDatabaseFieldManager(models.Manager):
    def create_new_public_database(self, data):
        new_public_database_field = self.create(
            fieldName = data["fieldName"],
            fieldDescription = data["fieldDescription"],
            fieldInUse =data["fieldInUse"],
            
        )
        return new_public_database_field
    

class PublicDatabaseField(models.Model):
    publicDatabaseID = models.ForeignKey(
                PublicDatabase,
                on_delete= models.CASCADE, null = True, blank = True)
    fieldName = models.CharField(max_length=50)
    fieldDescription = models.CharField(max_length= 400, null=True, blank=True)
    fieldInUse = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))

    #ManyToOne
    #public_database = models.ForeignKey(PublicDatabase, on_delete= models.CASCADE)
    
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
#       
class contributor_info(models.Model):
    hospital_name = CharField(max_length=150)
    admin_email = CharField(max_length=150)
    admin_telephone = CharField(max_length=50)
    admin_position = CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))

    class Meta:
        db_table = "ContributorsInfo"

    def __str__(self) :
        return "%s" % (self.hospital_name)

    def get_admin_email(self) :
        return "%s" % (self.admin_email)

    def get_admin_telephone(self) :
        return "%s" % (self.admin_telephone)

    def get_admin_position(self) :
        return "%s" % (self.admin_position)