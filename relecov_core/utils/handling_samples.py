from relecov_core.core_config import (
    HEADING_FOR_PUBLICDATABASEFIELDS_TABLE,
    HEADING_FOR_RECORD_SAMPLES,
    HEADINGS_FOR_ISkyLIMS,
    HEADING_FOR_AUTHOR_TABLE,
    HEADING_FOR_SAMPLE_TABLE,
    HEADINGS_FOR_ISkyLIMS_BATCH,
)
import json

from relecov_core.models import (
    Authors,
    Metadata,
    MetadataProperties,
    SchemaProperties,
    PropertyOptions,
    Schema,
    Sample,
    User,
)

from relecov_core.utils.rest_api_handling import (
    get_sample_fields_data,
    get_sample_project_fields_data,
)


def analyze_input_samples(request):
    sample_recorded = {}
    na_json_data = json.loads(request.POST["table_data"])
    process_rows = process_rows_in_json(na_json_data)

    if "wrong_rows" not in process_rows:
        insert_complete_rows(process_rows=process_rows)
        sample_recorded["process"] = "Success"
        sample_recorded["batch"] = fetch_batch_options()

    else:
        sample_recorded["process"] = "ERROR"
        sample_recorded["wrong_rows"] = process_rows["wrong_rows"]
        sample_recorded["sample"] = fetch_sample_options()

    return sample_recorded


def complete_sample_table_with_data_from_batch(data):
    sample = Sample.objects.filter(user_id=1, state_id=1).last()

    for field in data["sample_table"].items():
        sequencing_date_from_batch = field[1]

    sample.sequencing_date = sequencing_date_from_batch
    sample.state_id = 2
    sample.save()


def create_form_for_sample(schema_obj):
    """Collect information from iSkyLIMS and from metadata table to
    create the metadata form for filling sample data
    """
    import pdb; pdb.set_trace()
    schema_name = schema_obj.get_schema_name()
    m_form = []
    if not Metadata.objects.filter(
        metadata_name__iexact=schema_name, metadata_default=True
    ).exists():
        return m_form
    m_data_obj = Metadata.objects.filter(
        metadata_name__iexact=schema_name, metadata_default=True
    ).last()
    if not MetadataProperties.objects.filter(metadataID=m_data_obj).exists():
        return m_form
    m_field_objs = MetadataProperties.objects.filter(
        metadataID=m_data_obj, fill_mode__exact="sample"
    ).order_by("order")

    # get the sample fields and sample project fields from iSkyLIMS
    iskylims_sample_data = get_sample_fields_data()
    i_sam_proj_data = get_sample_project_fields_data()
    for m_field_obj in m_field_objs:
        field = {"label": m_field_obj.get_label()}
        if SchemaProperties.objects.filter(schemaID=schema_obj, label__iexact=field["label"]).exists():
            prop_obj = SchemaProperties.objects.filter(schemaID=schema_obj, label__iexact=field["label"]).last()
            field["format"] = prop_obj.get_format()

        if field["label"] in iskylims_sample_data:
            if isinstance(iskylims_sample_data["label"], list):
                field["options"] = iskylims_sample_data["label"]
            else:
                field["options"] = ""
        elif field["label"] in i_sam_proj_data:
            if isinstance(iskylims_sample_data["label"], list):
                field["options"] = iskylims_sample_data["label"]
            else:
                field["options"] = ""
        else:
            if PropertyOptions.objects.filter(propertyID=prop_obj.get_property_idj()).exists():
                prop_opt_objs = PropertyOptions.objects.filter(propertyID=prop_obj.get_property_idj())
                field["options"] = []
                for prop_opt_obj in prop_opt_objs:
                    field["options"].append(prop_opt_obj.get_enum())
            else:
                field["options"] = ""
        m_form.appemd(field)
    import pdb; pdb.set_trace()
    return m_form


def create_metadata_form(schema_obj):
    """Collect information from iSkyLIMS and from metadata table to
    create the user metadata fom
    """
    m_form = {}
    m_form["sample"] = create_form_for_sample(schema_obj)
    return m_form

    """ Code from Luis Aranda
    sample_recorded = {}
    sample_recorded["heading"] = [x[0] for x in HEADING_FOR_RECORD_SAMPLES]
    sample_recorded["batch"] = fetch_batch_options()
    sample_recorded["samples"] = fetch_sample_options()

    return sample_recorded
    """


def execute_query_to_sample_table(data):
    user = User.objects.get(id=1)
    data_sample = data["data_sample"]
    Sample.objects.create_new_sample(data=data_sample, user=user)

    # TODO - query to ISkyLIMS data
    # data_sample["data_ISkyLIMS"]


def execute_query_to_authors_table(data):
    data_authors = data["authors_table"]
    Authors.objects.create_new_authors(data_authors)


def execute_query_to_public_database_fields_table(data):
    # data_public_database_field = data["public_database_fields_table"]
    # PublicDatabaseField.objects.create_public_database_fields_table(data_public_database_field)
    pass


def fetch_batch_options():
    data = []
    headings = list(HEADING_FOR_RECORD_SAMPLES.values())

    # check schema
    schema_obj = Schema.objects.filter(
        schema_name="RELECOV", schema_default=True
    ).last()

    properties_objs = SchemaProperties.objects.filter(
        fill_mode="batch",
        schemaID=schema_obj,
    )

    for properties_obj in properties_objs:
        data_dict = {}
        if properties_obj.get_property() in headings:
            if properties_obj.has_options():
                data_dict["Options"] = list(
                    PropertyOptions.objects.filter(propertyID_id=properties_obj)
                    .values_list("enums", flat=True)
                    .distinct()
                )
            data_dict["Label"] = properties_obj.get_label()
            data_dict["Property"] = properties_obj.get_property()
            data_dict["Format"] = properties_obj.get_format()

            data.append(data_dict)

    return data


def fetch_sample_options():
    data = []
    schema_obj = Schema.objects.filter(
        schema_name="RELECOV", schema_default=True
    ).last()
    properties_objs = SchemaProperties.objects.filter(
        fill_mode="sample", schemaID=schema_obj
    )
    for properties_obj in properties_objs:
        data_dict = {}
        if properties_obj.has_options():
            data_dict["Options"] = list(
                PropertyOptions.objects.filter(propertyID_id=properties_obj)
                .values_list("enums", flat=True)
                .distinct()
            )
        data_dict["Label"] = properties_obj.get_label()
        data_dict["Property"] = properties_obj.get_property()
        data_dict["Format"] = properties_obj.get_format()
        data.append(data_dict)

    return data


def get_dropdown_options():
    properties = get_properties_dict()
    options = get_properties_options(properties)
    return options


def get_properties_dict():
    properties = (
        SchemaProperties.objects.filter(fill_mode="batch")
        .values_list("id", "property")
        .distinct()
    )
    properties_dict = dict(properties)

    return properties_dict


def get_properties_options(properties):
    properties_dict = {}
    for property in properties:
        options = (
            PropertyOptions.objects.filter(propertyID_id=property)
            .values_list("enums", flat=True)
            .distinct()
        )
        options_dict = list(options)
        properties_dict[property] = options_dict
    return options_dict


def get_sample_data(row):
    data = {}
    data_sample = {}
    data_ISkyLIMS = {}
    idx = 0
    headings = fetch_sample_options()
    sample_columns_names = sample_table_columns_names()

    # submittin_lab_sequencing_id => not found
    for heading in headings:
        if heading["Property"] in sample_columns_names:
            data_sample[heading["Property"]] = row[idx]
            idx += 1
        if heading["Label"] in HEADINGS_FOR_ISkyLIMS:
            data_ISkyLIMS[heading["Property"]] = row[idx]
            idx += 1
    data["data_sample"] = data_sample
    data["data_ISkyLIMS"] = data_ISkyLIMS

    return data


def insert_complete_rows(process_rows):
    complete_rows = process_rows["complete_rows"]
    if complete_rows is not None:
        for complete_row in complete_rows:
            data = get_sample_data(complete_row)
            execute_query_to_sample_table(data)


def metadata_sample_and_batch_is_completed(request):
    sample_data_inserted = []
    # Sample.objects.filter(state_id=1).delete()
    metadata_is_completed = Sample.objects.filter(
        user_id=request.user.id, state_id=1
    ).last()

    # check if a record about this user exits
    if metadata_is_completed is None:
        print(metadata_is_completed)
        request.session["pending_data_msg"] = "NOT PENDING DATA"

    elif metadata_is_completed is not None:
        print(metadata_is_completed)
        if metadata_is_completed.get_state() == "pre_recorded":
            sample_data_inserted = list(
                Sample.objects.filter(id=metadata_is_completed.id).values(
                    "collecting_lab_sample_id",
                    "sequencing_sample_id",
                    "biosample_accession_ENA",
                    "virus_name",
                    "gisaid_id",
                    "sequencing_date",
                )
            )
        if metadata_is_completed.__sizeof__() > 0:
            request.session["pending_data_list"] = sample_data_inserted
            request.session["pending_data_msg"] = "PENDING DATA"
    else:
        request.session["pending_data_msg"] = "NOT PENDING DATA"


def process_batch_metadata_form(request):
    data = {}
    data_sample = {}
    data_ISkyLIMS = {}
    data_authors = {}
    data_public_database_fields = {}
    headings = HEADING_FOR_RECORD_SAMPLES.values()
    for heading in headings:
        if heading in request.POST:
            if heading in HEADING_FOR_SAMPLE_TABLE.values():
                data_sample[heading] = request.POST[heading]
            if heading in HEADING_FOR_AUTHOR_TABLE.values():
                data_authors[heading] = request.POST[heading]
            if heading in HEADING_FOR_PUBLICDATABASEFIELDS_TABLE.values():
                data_public_database_fields[heading] = request.POST[heading]
            if heading in HEADINGS_FOR_ISkyLIMS_BATCH.values():
                data_ISkyLIMS[heading] = request.POST[heading]

    data["sample_table"] = data_sample
    data["authors_table"] = data_authors
    data["public_database_fields_table"] = data_public_database_fields
    data["sample_iskylims"] = data_ISkyLIMS

    return data


def process_rows_in_json(na_json_data):
    """
    This function:
     - checks that the first field is not empty, then
        - checks that the rest of the fields are not empty:
            1. If it finds one, it enters it in the "wrong_rows" list.
            2. If not empty fields, it enters it in the "complete_rows" list

    returns a dictionary:
        process_rows["wrong_rows"] = wrong_rows
        process_rows["complete_rows"] = complete_rows

    """
    wrong_rows = []
    complete_rows = []
    process_rows = {}

    for row in na_json_data:
        if row[0] == "":
            continue

        for field in range(len(row)):
            if row[field] == "":
                wrong_rows.append(row)
                break

        if "" not in row:
            complete_rows.append(row)

        if len(wrong_rows) > 0:
            process_rows["wrong_rows"] = wrong_rows
        process_rows["complete_rows"] = complete_rows

    return process_rows


def sample_table_columns_names():
    """
    This function returns a list containing the names of the columns of the Sample table
    """
    sample_table_columns_names = []
    for field in Sample._meta.fields:
        sample_table_columns_names.append(field.get_attname_column()[1])

    return sample_table_columns_names
