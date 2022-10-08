import json
from collections import OrderedDict
from django.contrib.auth.models import User, Group

# from django.db.models import Max

from relecov_core.core_config import (
    ALLOWED_EMPTY_FIELDS_IN_METADATA_SAMPLE_FORM,
    ERROR_FIELDS_FOR_METADATA_ARE_NOT_DEFINED,
    ERROR_ISKYLIMS_NOT_REACHEABLE,
    ERROR_NOT_ALLOWED_TO_SEE_THE_SAMPLE,
    ERROR_NOT_SAMPLES_HAVE_BEEN_DEFINED,
    ERROR_NOT_SAMPLES_STATE_HAVE_BEEN_DEFINED,
    ERROR_SAMPLE_DOES_NOT_EXIST,
    FIELD_FOR_GETTING_SAMPLE_ID,
    HEADING_FOR_BASIC_SAMPLE_DATA,
    HEADING_FOR_FASTQ_SAMPLE_DATA,
    HEADING_FOR_GISAID_SAMPLE_DATA,
    HEADING_FOR_ENA_SAMPLE_DATA,
    # HEADING_FOR_PUBLICDATABASEFIELDS_TABLE,
    # HEADING_FOR_RECORD_SAMPLES,
    # HEADINGS_FOR_ISkyLIMS,
    # HEADING_FOR_AUTHOR_TABLE,
    # HEADING_FOR_SAMPLE_TABLE,
    # HEADINGS_FOR_ISkyLIMS_BATCH,
)


from relecov_core.models import (
    DateUpdateState,
    MetadataVisualization,
    SchemaProperties,
    Sample,
    SampleState,
    TemporalSampleStorage,
)

from relecov_core.utils.handling_lab import get_lab_name

from relecov_core.utils.rest_api_handling import (
    get_sample_fields_data,
    get_sample_project_fields_data,
    get_sample_information,
    # save_sample_form_data,
)


def analyze_input_samples(request):
    result = {}
    save_samples = []
    s_already_record = []
    s_incomplete = []
    s_json_data = json.loads(request.POST["table_data"])
    heading_in_form = request.POST["heading"].split(",")
    l_metadata = request.POST["l_metadata"].split(",")
    l_iskylims = request.POST["l_iskylims"].split(",")
    # Select the sample field that will be used in Sample class
    idx_sample = heading_in_form.index(FIELD_FOR_GETTING_SAMPLE_ID)
    allowed_empty_index = []
    for item in ALLOWED_EMPTY_FIELDS_IN_METADATA_SAMPLE_FORM:
        allowed_empty_index.append(heading_in_form.index(item))
    for row in s_json_data:
        row_data = {}
        sample_name = row[idx_sample]
        if sample_name == "":
            continue
        if Sample.objects.filter(sequencing_sample_id__iexact=sample_name).exists():
            s_already_record.append(row)
            continue
        for idx in range(len(heading_in_form)):
            if row[idx] == "" and idx not in allowed_empty_index:
                s_incomplete.append(row)
                break
            if heading_in_form[idx] in l_metadata:
                idj = l_metadata.index(heading_in_form[idx])
                row_data[l_iskylims[idj]] = row[idx]
            else:
                row_data[heading_in_form[idx]] = row[idx]
        save_samples.append(row_data)

    if len(save_samples) > 0:
        result["save_samples"] = save_samples
    if len(s_incomplete) > 0:
        result["s_incomplete"] = s_incomplete
    if len(s_already_record) > 0:
        result["s_already_record"] = s_already_record
    return result


def count_samples_in_all_tables():
    """Count the number of entries that are in Sample,"""
    data = {}
    data["received"] = Sample.objects.all().count()
    # data["ena"] = EnaInfo.objects.all().count()
    # data["gisaid"] = GisaidInfo.objects.all().count()
    # data["processed"] = AnalysisPerformed.objects.filter(
    #    typeID__type_name__iexact="bioinfo_analysis"
    # ).count()
    return data


def create_form_for_batch(schema_obj, user_obj):
    """Collect information for creating for batch from. This form is displayed
    only if previously was defined sample in sample form
    """
    schema_name = schema_obj.get_schema_name()
    try:
        iskylims_sample_raw = get_sample_fields_data()
    except AttributeError:
        return {"ERROR": ERROR_ISKYLIMS_NOT_REACHEABLE}
    if "ERROR" in iskylims_sample_raw:
        return iskylims_sample_raw
    i_sam_proj_raw = get_sample_project_fields_data(schema_name)
    i_sam_proj_data = {}
    # Create the structure from the sample project fields get from iSkyLIMS
    for item in i_sam_proj_raw:
        key = item["sampleProjectFieldDescription"]
        i_sam_proj_data[key] = {}
        i_sam_proj_data[key]["format"] = item["sampleProjectFieldType"]
        if item["sampleProjectFieldType"] == "Options List":
            i_sam_proj_data[key]["options"] = []
            for opt in item["sampleProjectOptionList"]:
                i_sam_proj_data[key]["options"].append(opt["optionValue"])
    if not MetadataVisualization.objects.filter(fill_mode="sample").exists():
        return {"ERROR": ERROR_FIELDS_FOR_METADATA_ARE_NOT_DEFINED}
    m_batch_objs = MetadataVisualization.objects.filter(fill_mode="batch").order_by(
        "order"
    )

    m_batch_form = {}
    field_data = {}
    for m_batch_obj in m_batch_objs:
        label = m_batch_obj.get_label()
        field_data[label] = {}

        if label in i_sam_proj_data:
            field_data[label]["format"] = i_sam_proj_data[label]["format"]
            if "options" in i_sam_proj_data[label]:
                field_data[label]["options"] = i_sam_proj_data[label]["options"]
        else:
            print("The field not be recorded in iSkyLIMS", label)

    m_batch_form["fields"] = field_data
    m_batch_form["username"] = user_obj.username
    m_batch_form["lab_name"] = get_lab_name(user_obj)

    sample_objs = TemporalSampleStorage.objects.filter(user=user_obj)
    for sample_obj in sample_objs:
        pass

    return m_batch_form


def create_form_for_sample(schema_obj):
    """Collect information from iSkyLIMS and from metadata table to
    create the metadata form for filling sample data
    """
    # schema_name = schema_obj.get_schema_name()
    m_form = OrderedDict()
    f_data = {}
    l_iskylims = []  # variable name in iSkyLIMS
    l_metadata = []  # label in the form
    if not MetadataVisualization.objects.filter(fill_mode="sample").exists():
        return {"ERROR": ERROR_FIELDS_FOR_METADATA_ARE_NOT_DEFINED}
    m_sam_objs = MetadataVisualization.objects.filter(fill_mode="sample").order_by(
        "order"
    )
    # schema_obj = m_sam_objs[0].get_schema_obj()
    schema_name = schema_obj.get_schema_name()
    # Get the properties in schema for mapping
    s_prop_objs = SchemaProperties.objects.filter(schemaID=schema_obj)
    s_prop_dict = {}
    for s_prop_obj in s_prop_objs:
        if s_prop_obj.get_ontology() == "0":
            continue
        s_prop_dict[s_prop_obj.get_ontology()] = {
            "label": s_prop_obj.get_label(),
            "format": s_prop_obj.get_format(),
        }

    # get the sample fields and sample project fields from iSkyLIMS
    try:
        iskylims_sample_raw = get_sample_fields_data()
    except AttributeError:
        return {"ERROR": ERROR_ISKYLIMS_NOT_REACHEABLE}
    if "ERROR" in iskylims_sample_raw:
        return iskylims_sample_raw

    i_sam_proj_raw = get_sample_project_fields_data(schema_name)
    i_sam_proj_data = {}
    # Format the information from sample Project to have label as key
    # format of the field and the option list in aa list
    for item in i_sam_proj_raw:
        key = item["sampleProjectFieldDescription"]
        i_sam_proj_data[key] = {}
        i_sam_proj_data[key]["format"] = item["sampleProjectFieldType"]
        if item["sampleProjectFieldType"] == "Options List":
            i_sam_proj_data[key]["options"] = []
            for opt in item["sampleProjectOptionList"]:
                i_sam_proj_data[key]["options"].append(opt["optionValue"])
    # Map fields using ontology
    iskylims_sample_data = {}
    for key, values in iskylims_sample_raw.items():
        if "ontology" in values:
            try:
                label = s_prop_dict[values["ontology"]]["label"]
                iskylims_sample_data[label] = {}
                # Collect information to send back the values to iSkyLIMS
                l_iskylims.append(values["field_name"])
                l_metadata.append(label)
                if "options" in values:
                    iskylims_sample_data[label]["options"] = values["options"]
            except KeyError as e:
                print("Error in map ontology ", e)

    # Prepare for each label the information to show in form
    # Exclude the Originating Laboratory because value is fetched from user
    # profilc.
    # Exclude Submitting Institution becaue it is fixed to ISCIII
    exclude_fields = ["Originating Laboratory", "Submitting Institution"]
    for m_sam_obj in m_sam_objs:
        label = m_sam_obj.get_label()
        if label in exclude_fields:
            continue
        m_form[label] = {}

        if label in i_sam_proj_data:
            m_form[label]["format"] = i_sam_proj_data[label]["format"]
            if "options" in i_sam_proj_data[label]:
                m_form[label]["options"] = i_sam_proj_data[label]["options"]
        elif label in iskylims_sample_data:
            if "options" in iskylims_sample_data[label]:
                m_form[label]["options"] = iskylims_sample_data[label]["options"]
        else:
            print("The field not be recorded in iSkyLIMS", label)
        if "date" in label.lower():
            m_form[label]["format"] = "date"
        # check label belongs to iskylims to get t
    f_data["heading"] = ",".join(list(m_form.keys()))
    f_data["data"] = m_form
    f_data["l_iskylims"] = ",".join(l_iskylims)
    f_data["l_metadata"] = ",".join(l_metadata)
    return f_data


def create_metadata_form(schema_obj, user_obj):
    """Collect information from iSkyLIMS and from metadata table to
    create the user metadata fom
    """
    # Check if Fields for metadata Form are defiened
    if not MetadataVisualization.objects.all().exists():
        return {"ERROR": ERROR_FIELDS_FOR_METADATA_ARE_NOT_DEFINED}
    m_form = {}
    m_form["sample"] = create_form_for_sample(schema_obj)
    if "ERROR" in m_form["sample"]:
        return m_form["sample"]
    m_form["username"] = user_obj.username
    m_form["lab_name"] = get_lab_name(user_obj)
    return m_form


def get_friend_list(user_name):
    friend_list = []
    user_groups = user_name.groups.values_list("name", flat=True)
    if len(user_groups) > 0:
        for user in user_groups:
            if User.objects.filter(username__exact=user).exists():
                # friend_list.append(User.objects.get(username__exact = user).id)
                friend_list.append(User.objects.get(username__exact=user))

    friend_list.append(user_name)
    return friend_list


def get_sample_display_data(sample_id, user):
    """Check if user is allow to see the data and if true collect all info
    from sample to display
    """
    if not Sample.objects.filter(pk__exact=sample_id).exists():
        return {"ERROR": ERROR_SAMPLE_DOES_NOT_EXIST}
    group = Group.objects.get(name="RelecovManager")
    if group not in user.groups.all():
        if not Sample.objects.filter(pk__exact=sample_id, user=user).exists():
            f_list = get_friend_list(user)
            if not Sample.objects.filter(pk__exact=sample_id, user__in=f_list).exists():
                return {"ERROR": ERROR_NOT_ALLOWED_TO_SEE_THE_SAMPLE}
    sample_obj = Sample.objects.filter(pk__exact=sample_id).last()
    s_data = {}

    s_data["basic"] = list(
        zip(HEADING_FOR_BASIC_SAMPLE_DATA, sample_obj.get_sample_basic_data())
    )
    s_data["fastq"] = list(
        zip(HEADING_FOR_FASTQ_SAMPLE_DATA, sample_obj.get_fastq_data())
    )
    # Fetch actions done on the sample
    if DateUpdateState.objects.filter(sampleID=sample_obj).exists():
        actions = []
        actions_date_objs = DateUpdateState.objects.filter(
            sampleID=sample_obj
        ).order_by("-date")
        for action_date_obj in actions_date_objs:
            actions.append(
                [action_date_obj.get_state_name(), action_date_obj.get_date()]
            )
        s_data["actions"] = actions
    # Fetch gisaid and ena information
    gisaid_data = sample_obj.get_gisaid_info()
    if gisaid_data is not None:
        s_data["gisaid"] = list(zip(HEADING_FOR_GISAID_SAMPLE_DATA, gisaid_data))
    ena_data = sample_obj.get_ena_info()
    if ena_data != "":
        s_data["ena"] = list(zip(HEADING_FOR_ENA_SAMPLE_DATA, gisaid_data))
    lab_sample = sample_obj.get_collecting_lab_sample_id()
    # Fetch information from iSkyLIMS
    if lab_sample != "":
        iskylims_data = get_sample_information(lab_sample)
        if "ERROR" not in iskylims_data:
            s_data["iskylims_basic"] = list(
                zip(iskylims_data["heading"], iskylims_data["s_basic"])
            )
            s_data["iskylims_p_data"] = list(
                zip(
                    iskylims_data["sample_project_field_heading"],
                    iskylims_data["sample_project_field_value"],
                )
            )
            s_data["iskylims_project"] = iskylims_data["sample_project_name"]
    return s_data


def get_sample_obj_from_sample_name(sample_name):
    """Return the sample instance from its name"""
    if Sample.objects.filter(sequencing_sample_id__exact=sample_name).exists():
        return Sample.objects.filter(sequencing_sample_id__exact=sample_name).last()
    return None


def get_sample_obj_from_id(sample_id):
    """Return the sample instance from its id"""
    if Sample.objects.filter(pk__exact=sample_id).exists():
        return Sample.objects.filter(pk__exact=sample_id).last()
    return None


def get_samples_count_per_schema(schema_name):
    """Get the number of samples that are stored in the schema"""
    return Sample.objects.filter(schema_obj__schema_name__iexact=schema_name).count()


def get_search_data():
    """Fetch data to show in form"""

    if Sample.objects.count() == 0:
        return {"ERROR": ERROR_NOT_SAMPLES_HAVE_BEEN_DEFINED}
    s_state_objs = SampleState.objects.all()
    if len(s_state_objs) == 0:
        return {"ERROR": ERROR_NOT_SAMPLES_STATE_HAVE_BEEN_DEFINED}
    s_data = {"s_state": []}
    for s_state_obj in s_state_objs:
        s_data["s_state"].append(s_state_obj.get_state())
    return s_data


def increase_unique_value(old_unique_number):
    """The function increases in one number the unique value
    If number reaches the 9999 then the letter is stepped
    """
    split_value = old_unique_number.split("-")
    number = int(split_value[1]) + 1
    letter = split_value[0]

    if number > 9999:
        number = 1
        index_letter = list(split_value[0])
        if index_letter[2] == "Z":
            if index_letter[1] == "Z":
                index_letter[0] = chr(ord(index_letter[0]) + 1)
                index_letter[1] = "A"
                index_letter[2] = "A"
            else:
                index_letter[1] = chr(ord(index_letter[1]) + 1)
                index_letter[2] = "A"

            index_letter = "".join(index_letter)
        else:
            index_letter[2] = chr(ord(index_letter[2]) + 1)

        letter = "".join(index_letter)

    number_str = str(number)
    number_str = number_str.zfill(4)
    return str(letter + "-" + number_str)


def pending_samples_in_metadata_form(user_obj):
    """Check if there are samples waiting to be completed for the metadata form"""
    if TemporalSampleStorage.objects.filter(user=user_obj).exists():
        return True
    return False


def search_samples(sample_name, user_name, sample_state, s_date, user):
    """Search the samples that match with the query conditions"""
    sample_list = []
    sample_objs = Sample.objects.all()
    group = Group.objects.get(name="RelecovManager")
    if group not in user.groups.all():
        if user_name != "":
            if User.objects.filter(username__exact=user_name).exists():
                user_name_obj = User.objects.filter(username__exact=user_name).last()
                user_friend_list = get_friend_list(user_name_obj)
                if not sample_objs.filter(user__in=user_friend_list).exists():
                    return sample_list
                else:
                    sample_objs = sample_objs.filter(user__in=user_friend_list)
            else:
                return sample_list
    if sample_name != "":
        if sample_objs.filter(sequencing_sample_id__iexact=sample_name).exists():
            sample_objs = sample_objs.filter(sequencing_sample_id__iexact=sample_name)
            if len(sample_objs) == 1:
                sample_list.append(sample_objs[0].get_sample_id())
                return sample_list

        elif sample_objs.filter(sequencing_sample_id__icontains=sample_name).exists():
            sample_objs = sample_objs.filter(
                sequencing_sample_id__icontains=sample_name
            )
            if len(sample_objs) == 1:
                sample_list.append(sample_objs[0].get_sample_id())
                return sample_list
        else:
            return sample_list
    if sample_state != "":
        sample_objs = sample_objs.filter(state__state__exact=sample_state)

    if s_date != "":
        sample_objs = sample_objs.filter(created_at__exact=s_date)
    if len(sample_objs) == 1:
        sample_list.append(sample_objs[0].get_sample_id())
        return sample_list
    for sample_obj in sample_objs:
        sample_list.append(sample_obj.get_info_for_searching())
    return sample_list


def save_temp_sample_data(samples, user_obj):
    """Store the valid sample into the temporary table"""
    # get the latest value of sample_index
    """
    last_value = TemporalSampleStorage.objects.aggregate(Max("sample_idx")).get(
        "sample_idx__max"
    )
    if last_value is None:
        last_value = 0
    """
    sample_saved_list = []
    for sample in samples:
        # last_value += 1
        for item, value in sample.items():
            data = {"sample_name": sample[FIELD_FOR_GETTING_SAMPLE_ID]}
            data["field"] = item
            data["value"] = value
            data["user"] = user_obj
            TemporalSampleStorage.objects.save_temp_data(data)
        sample_saved_list.append(sample[FIELD_FOR_GETTING_SAMPLE_ID])
    return
