import json
import re
from relecov_core.models import (
    BioinfoProcessField,
    Classification,
    MetadataVisualization,
    PropertyOptions,
    Schema,
    SchemaProperties,
)
from relecov_core.utils.generic_functions import store_file, get_configuration_value
from relecov_core.core_config import (
    # SCHEMAS_UPLOAD_FOLDER,
    BIOINFO_UPLOAD_FOLDER,
    ERROR_INVALID_JSON,
    # ERROR_INVALID_SCHEMA,
    # ERROR_SCHEMA_ALREADY_LOADED,
    # SCHEMA_SUCCESSFUL_LOAD,
    ERROR_SCHEMA_ID_NOT_DEFINED,
    ERROR_SCHEMA_NOT_DEFINED,
    HEADING_SCHEMA_DISPLAY,
    # MAIN_SCHEMA_STRUCTURE,
    NO_SELECTED_LABEL_WAS_DONE,
)
from django.db import models


# "caller" field parsed by Erika
def fetch_bioinfo_data(data):
    registers = BioinfoProcessField.objects.all()
    registers.delete()

    list_of_properties = []
    list_of_values = []
    list_of_no_exists = []
    # number_of_sample = data.keys()
    data_in_sample = data.values()

    for dat in data_in_sample:
        list_of_properties = list(dat.keys())
        list_of_values = list(dat.values())

    for property in list_of_properties:
        if SchemaProperties.objects.filter(property__iexact=property).exists():
            print("Exists in Schema")
            if BioinfoProcessField.objects.filter(
                property_name__iexact=property
            ).exists():
                pass
            else:
                data_fields = SchemaProperties.objects.filter(
                    property__iexact=property
                ).values_list("schemaID", "label", "classification")
                print(data_fields)
                schema_id = Schema.objects.get(schema_default=1)

                instance = BioinfoProcessField.objects.create(
                    property_name=property,
                    label_name=data_fields[0][1],
                    classificationID=Classification.objects.get(
                        class_name=data_fields[0][2]
                    ),
                )
                instance.schemaID.add(schema_id)
                instance.save()

        else:
            print("Doesn't exist in Schema: " + str(property))
            list_of_no_exists.append(property)
    print(len(list_of_no_exists))
    print(list_of_no_exists)
    """
            data_fields = SchemaProperties.objects.filter(
                property__iexact=property
            ).values_list("schemaID", "label", "classification")

            schema_id = Schema.objects.get(schema_default=1)

            instance = BioinfoProcessField.objects.create(
                property_name=property,
                label_name=data_fields[0][1],
                classificationID=Classification.objects.get(
                    class_name=data_fields[0][2]
                ),
            )
            instance.schemaID.add(schema_id)
            instance.save()
    """
    # property_in_schema = SchemaProperties.objects.get(property=property)
    # print(property_in_schema)


####################bioinfo file#####################################
def load_bioinfo_file(json_file):
    """Store json file in the defined folder and store information in database"""
    data = {}
    try:
        data["full_bioinfo"] = json.load(json_file)
    except json.decoder.JSONDecodeError:
        return {"ERROR": ERROR_INVALID_JSON}
    data["file_name"] = store_file(json_file, BIOINFO_UPLOAD_FOLDER)
    return data


def store_bioinfo_fields(schema_obj, s_properties):
    """Store the fields to be used for saving analysis information"""
    for prop_key in s_properties.keys():
        data = dict(s_properties[prop_key])
        if "classification" in data:
            match = re.search(r"(\w+) fields", data["classification"])
            if not match:
                continue
            classification = match.group(1).strip()
            # create new entr in Classification table in not exists
            if Classification.objects.filter(
                class_name__iexact=classification
            ).exists():
                class_obj = Classification.objects.filter(
                    class_name__iexact=classification
                ).last()
            else:
                class_obj = Classification.objects.create_new_classification(
                    classification
                )
            fields = {}
            fields["classificationID"] = class_obj
            fields["property_name"] = prop_key
            fields["label_name"] = data["label"]
            n_field = BioinfoProcessField.objects.create_new_field(fields)
            n_field.schemaID.add(schema_obj)

    return {"SUCCESS": ""}


def process_bioinfo_file(json_file, user, apps_name):
    """Check json file and store in database"""
    list_of_samples = []
    list_of_samples_values = []
    list_of_samples_properties = []
    bioinfo_data = load_bioinfo_file(json_file)
    list_of_samples = bioinfo_data["full_bioinfo"].keys()
    print(list_of_samples_values)
    for sample in bioinfo_data["full_bioinfo"]:
        list_of_samples_values = bioinfo_data["full_bioinfo"][sample].values()
        list_of_samples_properties = bioinfo_data["full_bioinfo"][sample].keys()
        print(list_of_samples_properties)

        for property in list_of_samples_properties:

            schema_id = Schema.objects.get(schema_default=1)

            instance = BioinfoProcessField.objects.create(
                property_name=property,
                label_name="labela",
                classificationID=Classification.objects.get(class_name="Sequencing"),
            )
            instance.schemaID.add(schema_id)
            instance.save()
        break
    """
    return {"SUCCESS": SCHEMA_SUCCESSFUL_LOAD}
    """


def set_chromosome(data):
    chrom_id = 0
    if Chromosome.objects.filter(chromosome=data["Chrom"]["chromosome"]).last():
        chrom_id = (
            Chromosome.objects.filter(chromosome=data["Chrom"]["chromosome"]).last()
            # .get_chromosome_id()
        )

        return chrom_id

    else:
        chrom_serializer = CreateChromosomeSerializer(data=data["Chrom"])
        if chrom_serializer.is_valid():
            chrom_serializer.save()
            print("chrom_serializer saved")


def set_gene(data):
    gene_id = 0
    if Gene.objects.filter(gene__iexact=data["Gene"]["gene"]).exists():
        gene_id = (
            Gene.objects.filter(gene__iexact=data["Gene"]["gene"]).last()
            # .get_gene_id()
        )
        return gene_id
    else:
        gene_serializer = CreateGeneSerializer(data=data["Gene"]["gene"])
        if gene_serializer.is_valid():
            gene_serializer.save()
            print("gene_serializer saved")


def set_effect(data):
    effect_id = 0
    if Effect.objects.filter(effect__iexact=data["Effect"]["effect"]).exists():
        effect_id = (
            Effect.objects.filter(effect__iexact=data["Effect"]["effect"]).last()
            # .get_effect_id()
        )
        return effect_id
    else:
        effect_serializer = CreateEffectSerializer(data=data["Effect"])
        if effect_serializer.is_valid():
            effect_serializer.save()
            print("effect_serializer saved")


def set_variant_in_sample(data):
    variant_in_sample_id = 0
    if VariantInSample.objects.filter(
        dp__iexact=data["VariantInSample"]["dp"]
    ).exists():
        variant_in_sample_id = (
            VariantInSample.objects.filter(
                dp__iexact=data["VariantInSample"]["dp"]
            ).last()
            # .get_variant_in_sample_id()
        )
        return variant_in_sample_id
    else:
        variant_in_sample_serializer = CreateVariantInSampleSerializer(
            data=data["VariantInSample"]
        )
        if variant_in_sample_serializer.is_valid():
            variant_in_sample_serializer.save()
            print("variant_in_sample_serializer saved")


def set_filter(data):
    filter_id = 0
    if Filter.objects.filter(filter__iexact=data["Filter"]["filter"]).exists():
        filter_id = (
            Filter.objects.filter(filter__iexact=data["Filter"]["filter"]).last()
            # .get_filter_id()
        )
        return filter_id
    else:
        filter_serializer = CreateFilterSerializer(data=data["Filter"])
        if filter_serializer.is_valid():
            filter_serializer.save()
            print("filter_serializer saved")


def set_position(data):
    position_id = 0
    if Position.objects.filter(pos__iexact=data["Position"]["pos"]).exists():
        position_id = (
            Position.objects.filter(pos__iexact=data["Position"]["pos"]).last()
            # .get_position_id()
        )
        return position_id
    else:
        position_serializer = CreatePositionSerializer(data=data["Position"])
        if position_serializer.is_valid():
            position_serializer.save()
            print("position_serializer saved")


def set_sample(data):
    sample_id = 0
    if Sample.objects.filter(
        collecting_lab_sample_id=data["Sample"]["collecting_lab_sample_id"]
    ).exists():
        sample_id = (
            Sample.objects.filter(
                collecting_lab_sample_id=data["Sample"]["collecting_lab_sample_id"]
            ).last()
            # .get_sample_id()
        )

        return sample_id
    """
    else:
        sample_serializer = CreateSampleSerializer(data=data["Sample"])
        if sample_serializer.is_valid():
            sample_serializer.save()
            print("sample_serializer saved")
    """


def set_variant(data, data_ids):
    if Variant.objects.filter(ref__iexact=data["Variant"]["ref"]).exists():
        variant_id = (
            Variant.objects.filter(ref__iexact=data["Variant"]["ref"])
            .last()
            .get_variant_id()
        )
        return variant_id
    else:
        variant = Variant.objects.create_new_variant(data["Variant"]["ref"], data_ids)
        variant.save()

        """
        variant_serializer = CreateVariantSerializer(data=data["Variant"])
        print(variant_serializer)
        if variant_serializer.is_valid():
            variant_serializer.save()
            print("variant_serializer saved")
        """


def set_lineage(data):
    lineage_id = 0
    if Lineage.objects.filter(
        lineage_name__iexact=data["Lineage"]["lineage_name"]
    ).exists():
        lineage_id = (
            Lineage.objects.filter(lineage_name__iexact=data["Lineage"]["lineage_name"])
            .last()
            .get_lineage_id()
        )
        return lineage_id
    else:
        new_lineage = Lineage.objects.create(
            lineage_name=data["Lineage"]["lineage_name"]
        )
        new_lineage.save()
        """
        lineage_serializer = CreateLineageSerializer(
            data=data["Lineage"]["lineage_name"]
        )
        if lineage_serializer.is_valid():
            lineage_serializer.save()
            print("lineage_serializer saved")
        """


# this function creates a new Sample register for testing
def create_sample_register():
    new_sample = Sample.objects.create(
        state=SampleState.objects.create(
            state="pre-recorded",
            display_string="display_string",
            description="description",
        ),
        user=User.objects.create(password="appapk", username="tere"),
        metadata_file=Document.objects.create(
            title="title", file_path="", uploadedFile=""
        ),
        collecting_lab_sample_id="200002",
        sequencing_sample_id="1234",
        biosample_accession_ENA="456123",
        virus_name="ramiro",
        gisaid_id="09876",
        sequencing_date="2022/8/2",
    )
    new_sample.save()
