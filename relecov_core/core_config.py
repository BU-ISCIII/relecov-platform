ALLOWED_EMPTY_FIELDS_IN_METADATA_SAMPLE_FORM = [
    "Public Health sample id (SIVIES)",
    "GISAID id",
    "GISAID Virus Name",
    "Sequence file R2 fastq",
]
SCHEMAS_UPLOAD_FOLDER = "schemas"
BIOINFO_UPLOAD_FOLDER = ""

SCHEMA_SUCCESSFUL_LOAD = "Schema was successfully loaded"
BIOINFO_SUCCESSFUL_LOAD = "Bioinfo file was successfully loaded"
BIOINFO_METADATA_SUCCESSFUL_LOAD = "Bioinfo metadata file was successfully loaded"
METADATA_JSON_SUCCESSFUL_LOAD = "Metadata was successfully loaded"
ERROR_SCHEMA_ID_NOT_DEFINED = "schema ID is not defined"
ERROR_SCHEMA_NOT_DEFINED = "No schemas have been defined yet"
ERROR_SAMPLE_NAME_NOT_INCLUDED = "Sample name field is not included in the request"
ERROR_SAMPLE_NOT_DEFINED = "Sample id is not defined"
ERROR_SAMPLES_NOT_DEFINED_IN_FORM = (
    "Samples were not defined when loading data for batch "
)
ERROR_ANALYSIS_ALREADY_DEFINED = "Analysis is already defined."
ERROR_NO_SAMPLES_ARE_ASSIGNED_TO_LAB = "There is no sample recorded for laboratory"
ERROR_NOT_SAMPLES_HAVE_BEEN_DEFINED = "So far there are no samples defined"
ERROR_NOT_SAMPLES_STATE_HAVE_BEEN_DEFINED = "Missing configuration for sample states"
ERROR_GENE_NOT_DEFINED_IN_DATABASE = "Error Gene not defined in database"
ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE = "Error Chromosome not defined in database"
ERROR_USER_IS_NOT_ASSIGNED_TO_LAB = "Your account is not assigned to any laboratory"
ERROR_INVALID_DEFINED_SAMPLE_FORMAT = "The format for the defined Date is incorrect"
ERROR_NOT_MATCHED_ITEMS_IN_SEARCH = "Your query does not return any match"

ERROR_SAMPLE_DOES_NOT_EXIST = "The Sample you request does not exist"
ERROR_CHROMOSOME_DOES_NOT_EXIST = "The Chromosome you request does not exist"
ERROR_NOT_ALLOWED_TO_SEE_THE_SAMPLE = "You are not allowed to see the sample"

ERROR_INVALID_JSON = "Invalid json file"
ERROR_INVALID_SCHEMA = "Invalid Schema"
ERROR_SCHEMA_ALREADY_LOADED = "Schema is already loaded"

ERROR_INTIAL_SETTINGS_NOT_DEFINED = "Relecov Platform is not fully completed"
ERROR_FIELDS_FOR_METADATA_ARE_NOT_DEFINED = (
    "Fields to display in Metadata form are not defined yet"
)
ERROR_ISKYLIMS_NOT_REACHEABLE = "iSkyLIMS server is not accessible"
ERROR_FIELD_NOT_DEFINED = "Field is not defined in database"

ERROR_UNABLE_TO_STORE_IN_DATABASE = "Unable to store data in database "
ERROR_UNABLE_FETCH_SAMPLE_PROJECT_FIELDS = (
    "Unable to fetch project fields from iSkyLIMS "
)

ERROR_MISSING_SAMPLE_DATA = "Missing data information for Sample"

ERROR_ANNOTATION_ORGANISM_ALREADY_EXISTS = (
    "Annotation file for the organism already loaded"
)
ERROR_VARIANT_INFORMATION_NOT_DEFINED = "Variant field is not included in the request"
ERROR_VARIANT_IN_SAMPLE_NOT_DEFINED = "So far there is no variants defined on database "

HEADING_FOR_BASIC_SAMPLE_DATA = [
    "Sample ID given for sequencing",
    "Sample ID given in the microbiology lab",
    "Sample ID given by the submitting laboratory",
    "Sample State",
    "Recorded Date",
]
HEADING_FOR_FASTQ_SAMPLE_DATA = [
    "Sequence file R1 fastq",
    "Sequence file R2 fastq",
    "Filepath R1 fastq",
    "Filepath R2 fastq",
    "Fastq md5 r1",
    "Fastq md5 r2",
]
HEADING_SCHEMA_DISPLAY = [
    "Property",
    "Label",
    "Required",
    "Classification",
    "Description",
]

HEADING_FOR_ANNOTATION_GENE = ["Gene name", "Position start", "Position end"]

HEADING_FOR_SAMPLE_LIST = [
    "Sequencing Sample ID",
    "State",
    "Sequenced date",
    "Recorded date",
]
HEADING_FOR_VARIANT_TABLE_DISPLAY = [
    "Pos",
    "Ref",
    "Alt",
    "dp",
    "ref_dp",
    "alt_dp",
    "af",
    "hgvs_c",
    "hgvs_p",
    "hgvs_p_1_letter",
]
FIELD_FOR_GETTING_SAMPLE_ID = "Sample ID given for sequencing"

MAIN_SCHEMA_STRUCTURE = ["schema", "required", "type", "properties"]
NO_SELECTED_LABEL_WAS_DONE = (
    "No selected label order was done to define Metadata visualization"
)

ISKLIMS_REST_API = "/wetlab/api/"
# REST API TO iSkyLIMS
ISKLIMS_GET_LABORATORY_PARAMETERS = ["laboratoryData", "laboratory"]
ISKLIMS_PUT_LABORATORY_PARAMETER = "updateLab"
ISKLIMS_GET_SAMPLE_FIELDS = "sampleFields"
ISKLIMS_GET_SAMPLE_INFORMATION = ["fetchSampleIinformation", "sample"]
ISKLIMS_GET_SAMPLE_PROJECT_FIELDS = ["sampleProjectFields", "project"]
ISKLIMS_GET_SUMMARIZE_DATA = "summarizeDataInformation"
ISKLIMS_GET_STATS_DATA = "statisticsInformation"
ISKLIMS_FETCH_SAMPLES_ON_CONDITION = ["fetchSamplesOnParameter", "sampleParameter"]
ISKLIMS_POST_SAMPLE_DATA = "createSampleData"

# API requested information
FIELDS_ON_SAMPLE_TABLE = [
    "user",
    "collecting_lab_sample_id",
    "microbiology_lab_sample_id",
    "sequencing_sample_id",
    "submitting_lab_sample_id",
    "sequence_file_R1_fastq",
    "sequence_file_R2_fastq",
    "fastq_r1_md5",
    "fastq_r2_md5",
    "r1_fastq_filepath",
    "r2_fastq_filepath",
]
FIELDS_ON_ENA_TABLE = [
    "bioproject_accession_ENA",
    "bioproject_umbrella_accession_ENA",
    "biosample_accession_ENA",
    "GenBank_ENA_DDBJ_accession",
    "study_alias",
    "study_id",
    "experiment_title",
]
FIELDS_ON_GISAID_TABLE = ["gisaid_id", "GISAID_accession", "virus_name"]
FIELDS_ON_AUTHOR_TABLE = ["analysis_authors", "author_submitter", "authors"]
