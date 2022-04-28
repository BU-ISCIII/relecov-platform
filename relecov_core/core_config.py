#HEADING_FOR_RECORD_SAMPLES, HEADING_FOR_SAMPLE_TABLE, HEADING_FOR_LINEAGE_TABLE, HEADING_FOR_ANALYSIS
HEADING_FOR_RECORD_SAMPLES = [
    ("Public Health sample id (SIVIES)", "public_health_sample_id_sivies"),
    ("Sample ID given by originating laboratory", "collecting_lab_sample_id"),
    ("Sample ID given by the submitting laboratory", "submitting_lab_sample_id"),
    ("Sample ID given in the microbiology lab", "microbiology_lab_sample_id"),
    ("Sample ID given if multiple rna-extraction or passages", "isolate_sample_id"),
    ("Sample ID given for sequencing", "sequencing_sample_id"),
    ("Originating Laboratory", "collecting_lab_sample_id"),
    ("Sample Collection Date", "sample_collection_date"),
    ("Sample Received Date", "sample_received_date"),
    ("Specimen source", "anatomical_material"),
    ("Environmental Material", "environmental_material"),
    ("Host Age", "host_age"),
    ("Host Gender", "host_gender"),
    ("Sequence file R1 fastq", "sequence_file_R1_fastq"),
    ("Sequence file R2 fastq", "sequence_file_R2_fastq"),
]

HEADING_FOR_SAMPLE_TABLE = [
    ("Sample ID given by originating laboratory", "collecting_lab_sample_id"),
    ("Sample ID given for sequencing", "sequencing_sample_id"),
    ("ENA Sample Id", "biosample_accession_ENA"),
    ("GISAID Virus Name",  "virus_name"),
    ("GISAID Id", "gisaid_id"),
    ("Sequencing Date", "sequencing_date"),
]

HEADING_FOR_LINEAGE_TABLE = [
    ("Lineage identification date", "lineage_identification_date"),
    ("Lineage/clade name", "lineage_name"),
    ("Lineage/clade analysis software name", "lineage_analysis_software_name"),
    ("If lineage identification Is Other, Specify", "if_lineage_identification_other"),
    ("Lineage/clade analysis software version", "lineage_analysis_software_version"),
]

HEADING_FOR_ANALYSIS = [
    ("Raw sequence data processing method", "raw_sequence_data_processing_method"),
    ("Dehosting Method", "dehosting_method"),
    ("Assembly", "assembly"),
    ("If assembly Is Other, Specify", "if_assembly_other"),
    ("AssEmbly params", "assembly_params"),
    ("Variant Calling", "variant_calling"),
    ("If variant calling Is Other, Specify", "if_variant_calling_other"),
    ("Variant Calling params", "variant_calling_params"),
    ("Consensus sequence name", "consensus_sequence_name"),
    ("Consensus sequence name md5", "consensus_sequence_name_md5"),
    ("Consensus sequence filepath","consensus_sequence_filepath"),
    "Consensus sequence software name", "consensus_sequence_software_name",
    "If consensus Is Other, Specify", "if consensus other",
    "Consensus sequence software version", "consensus_sequence_software_version",
    "Consensus criteria", "consensus_criteria",
    "Reference genome accession", "reference_genome_accession",
    "Bioinformatics protocol", "bioinformatics_protocol",
    "If bioinformatic protocol Is Other, Specify", "if_bioinformatic_protocol_is_other_specify",
    "bioinformatics protocol version", "bioinformatic_protocol_version",
    "Analysis date", "analysis_date",
    "Commercial/Open-source/both", "commercial/open-source/both",
    "Preprocessing", "preprocessing",
    "If preprocessing Is Other, Specify", "if_preprocessing_other",
    "Preprocessing params", "preprocessing_params",
    "Mapping", "mapping",
    "If mapping Is Other, Specify", "if_mapping_other",
    "Mapping params", "mapping_params",
    "reference genome accession", "reference_genome_accession",
]

"""Para eliminar
HEADING_FOR_RECORD_SAMPLES = {
    "Public Health sample id (SIVIES)": "public_health_sample_id_sivies",
    "Sample ID given by originating laboratory": "collecting_lab_sample_id",
    "Sample ID given by the submitting laboratory": "submitting_lab_sample_id",
    "Sample ID given in the microbiology lab": "microbiology_lab_sample_id",
    "Sample ID given if multiple rna-extraction or passages": "isolate_sample_id",
    "Sample ID given for sequencing": "sequencing_sample_id",
    "Originating Laboratory": "collecting_lab_sample_id",
    "Sample Collection Date": "sample_collection_date",
    "Sample Received Date": "sample_received_date",
    "Specimen source": "anatomical_material",
    "Environmental Material": "environmental_material",
    "Host Age": "host_age",
    "Host Gender": "host_gender",
    "Sequence file R1 fastq": "sequence_file_R1_fastq",
    "Sequence file R2 fastq": "sequence_file_R2_fastq",
}

HEADING_FOR_SAMPLE_TABLE = {
    "Sample ID given by originating laboratory" : "collecting_lab_sample_id",
    "Sample ID given for sequencing" : "sequencing_sample_id",
    "ENA Sample Id" : "biosample_accession_ENA",
    "GISAID Virus Name" : "virus_name",
    "GISAID Id" : "gisaid_id",
    "Sequencing Date" : "sequencing_date",
}

HEADING_FOR_LINEAGE_TABLE = {
    "Lineage identification date" : "lineage_identification_date",
    "Lineage/clade name" : "lineage_name",
    "Lineage/clade analysis software name" : "lineage_analysis_software_name",
    "If lineage identification Is Other, Specify" : "if_lineage_identification_other",
    "Lineage/clade analysis software version" : "lineage_analysis_software_version",
}

HEADING_FOR_ANALYSIS = {
    "Raw sequence data processing method" : "raw_sequence_data_processing_method",
    "Dehosting Method" : "dehosting_method",
    "Assembly" : "assembly",
    "If assembly Is Other, Specify" : "if_assembly_other",
    "AssEmbly params" : "assembly_params",
    "Variant Calling" : "variant_calling",
    "If variant calling Is Other, Specify" : "if_variant_calling_other",
    "Variant Calling params" : "variant_calling_params",
    "Consensus sequence name" : "consensus_sequence_name",
    "Consensus sequence name md5" : "consensus_sequence_name_md5",
    "Consensus sequence filepath" : "consensus_sequence_filepath",
    "Consensus sequence software name" : "consensus_sequence_software_name",
    "If consensus Is Other, Specify" : "if consensus other",
    "Consensus sequence software version" : "consensus_sequence_software_version",
    "Consensus criteria" : "consensus_criteria",
    "Reference genome accession" : "reference_genome_accession",
    "Bioinformatics protocol" : "bioinformatics_protocol",
    "If bioinformatic protocol Is Other, Specify" : "if_bioinformatic_protocol_is_other_specify",
    "bioinformatics protocol version" : "bioinformatic_protocol_version",
    "Analysis date" : "analysis_date",
    "Commercial/Open-source/both" : "commercial/open-source/both",
    "Preprocessing" : "preprocessing",
    "If preprocessing Is Other, Specify" : "if_preprocessing_other",
    "Preprocessing params" : "preprocessing_params",
    "Mapping" : "mapping",
    "If mapping Is Other, Specify" : "if_mapping_other",
    "Mapping params" : "mapping_params",
    "reference genome accession" : "reference_genome_accession",
}
"""
"""
HEADING_FOR_SAMPLE_TABLE = [
    ("Sample ID given by originating laboratory", "collecting_lab_sample_id"),
    ("Sample ID given for sequencing", "sequencing_sample_id"),
]
"""
"""
HEADING_FOR_RECORD_SAMPLES = [
    ["Public Health sample id (SIVIES)", "public_health_sample_id_sivies"],
    ["Sample ID given by originating laboratory", "collecting_lab_sample_id"],
    ["Sample ID given by the submitting laboratory", "submitting_lab_sample_id"],
    ["Sample ID given in the microbiology lab", "microbiology_lab_sample_id"],
    ["Sample ID given if multiple rna-extraction or passages", "isolate_sample_id"],
    ["Sample ID given for sequencing", "sequencing_sample_id"],
    ["Originating Laboratory", "collecting_lab_sample_id"],
    ["Sample Collection Date", "sample_collection_date"]
    ["Sample Received Date", "sample_received_date"],
    ["Specimen source", "anatomical_material"],
    ["Environmental Material", "environmental_material"],
    ["Host Age", "host_age"],
    ["Host Gender", "host_gender"],
    ["Sequence file R1 fastq", "sequence_file_R1_fastq"],
    ["Sequence file R2 fastq", "sequence_file_R2_fastq"],
]
"""
"""
HEADING_FOR_RECORD_SAMPLE_IN_DATABASE = [
    "public_health_sample_id_sivies",
    "collecting_lab_sample_id",
    "submitting_lab_sample_id",
    "microbiology_lab_sample_id",
    "isolate_sample_id",
    "sequencing_sample_id",
    "collecting_lab_sample_id",
    "sample_collection_date",
    "sample_received_date",
    "anatomical_material",
    "environmental_material",
    "host_age",
    "host_gender",
    "sequence_file_R1_fastq",
    "sequence_file_R2_fastq",
    
]
"""
