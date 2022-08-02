import json
from collections import OrderedDict
from django.contrib.auth.models import User, Group

# from django.db.models import Max

from relecov_core.core_config import (
    ERROR_FIELDS_FOR_METADATA_ARE_NOT_DEFINED,
    FIELD_FOR_GETTING_SAMPLE_ID,
    ERROR_ISKYLIMS_NOT_REACHEABLE,
    ERROR_NOT_ALLOWED_TO_SEE_THE_SAMPLE,
    ERROR_NOT_SAMPLES_HAVE_BEEN_DEFINED,
    ERROR_NOT_SAMPLES_STATE_HAVE_BEEN_DEFINED,
    ERROR_SAMPLE_DOES_NOT_EXIST,
    HEADING_FOR_BASIC_SAMPLE_DATA,
    HEADING_FOR_FASTQ_SAMPLE_DATA,
    # HEADING_FOR_PUBLICDATABASEFIELDS_TABLE,
    # HEADING_FOR_RECORD_SAMPLES,
    # HEADINGS_FOR_ISkyLIMS,
    # HEADING_FOR_AUTHOR_TABLE,
    # HEADING_FOR_SAMPLE_TABLE,
    # HEADINGS_FOR_ISkyLIMS_BATCH,
)


from relecov_core.models import (
    # Authors,
    MetadataVisualization,
    SchemaProperties,
    #
    # TemporalSampleStorage,
    # PropertyOptions,
    # Schema,
    Sample,
    SampleState,
    # User,
)

from relecov_core.utils.rest_api_handling import (
    get_sample_fields_data,
    get_sample_project_fields_data,
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
    for row in s_json_data:
        row_data = {}
        sample_name = row[idx_sample]
        if sample_name == "":
            continue
        if Sample.objects.filter(sequencing_sample_id__iexact=sample_name).exists():
            s_already_record.append(row)
            continue
        for idx in range(len(heading_in_form)):
            if row[idx] == "":
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


def create_form_for_batch(schema_obj, user_obj):
    """Collect information for creating for batch from. This form is displayed
    only if previously was defined sample in sample form
    """
    b_form = []
    if Sample.objects.filter(
        state__state__exact="Pre-recorded", user=user_obj
    ).exists():
        s_objs = Sample.objects.filter(
            state__state__exact="Pre-recorded", user=user_obj
        )
        for s_obj in s_objs:
            pass
    return b_form


def create_form_for_sample(schema_obj):
    """Collect information from iSkyLIMS and from metadata table to
    create the metadata form for filling sample data
    """
    schema_name = schema_obj.get_schema_name()
    m_form = OrderedDict()
    f_data = {}
    l_iskylims = []  # variable name in iSkyLIMS
    l_metadata = []  # label in the form
    if not MetadataVisualization.objects.filter(fill_mode="sample").exists():
        return {"ERROR": ERROR_FIELDS_FOR_METADATA_ARE_NOT_DEFINED}
    m_sam_objs = MetadataVisualization.objects.filter(fill_mode="sample").order_by(
        "order"
    )
    schema_obj = m_sam_objs[0].get_schema_obj()
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

    i_sam_proj_raw = get_sample_project_fields_data(schema_name)
    i_sam_proj_data = {}
    # Format the information from sample Project to have label as key
    # format of the field and the option list in aa list
    for item in i_sam_proj_raw:
        key = item["sampleProjectFieldDescription"]
        i_sam_proj_data[key] = {}
        i_sam_proj_data[key]["format"] = item["sampleProjectFieldType"]
        if item["sampleProjectFieldType"] == "Option List":
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
                # Collcct information to send back the values ot iSkyLIMS
                l_iskylims.append(values["field_name"])
                l_metadata.append(label)
                if "options" in values:
                    iskylims_sample_data[label]["options"] = values["options"]
            except KeyError as e:
                print("Error in map ontology ", e)

    # Prepare for each label the information to show in form
    for m_sam_obj in m_sam_objs:
        label = m_sam_obj.get_label()
        m_form[label] = {}
        if label in i_sam_proj_data:
            m_form[label]["format"] = i_sam_proj_data[label]["format"]
            if "options" in i_sam_proj_data[label]:
                m_form[label]["options"] = i_sam_proj_data[label]["options"]
        elif label in iskylims_sample_data:
            if "options" in iskylims_sample_data[label]:
                m_form[label]["options"] = iskylims_sample_data[label]["options"]
        else:
            print("ERROR not found in iSkyLIMS", label)
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
    m_form["batch"] = create_form_for_batch(schema_obj, user_obj)
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

    return s_data


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


def search_samples(sample_name, user_name, sample_state, s_date):
    """Search the samples that match with the query conditions"""
    sample_list = []
    sample_objs = Sample.objects.all()
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


def save_temp_sample_data(samples):
    """Store the valid sample into the temporary table"""
    # get the latest value of sample_index
    """
    last_value = TemporalSampleStorage.objects.aggregate(Max("sample_idx")).get(
        "sample_idx__max"
    )
    if last_value is None:
        last_value = 0

    for sample in samples:
        last_value += 1
        for item, value in sample.items():
            data = {"sample_idx": last_value}
            data["field"] = item
            data["value"] = value
            TemporalSampleStorage.objects.save_temp_data(data)
    """
    return
