# Generic imports
import json
import os
import shutil
import hashlib
from collections import OrderedDict, defaultdict
from datetime import datetime
import pandas as pd
from django.contrib.auth.models import Group, User
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import Q
from django.db.models import Count
from django.db.models.functions import TruncDate
import relecov_tools.utils
from django.template.loader import render_to_string

# Local imports
import core.utils.plotly_dash_graphics
import core.config
import core.utils.labs
import core.utils.plotly_graphics
import core.utils.rest_api
import core.utils.generic_functions
import core.models
import dashboard.utils.generic_graphic_data


def get_iskylims_project_field_display_map(project_name):
    """Return a map from iSkyLIMS project field key to display label."""
    if isinstance(project_name, dict):
        project_name = project_name.get("value")
    if not project_name:
        return {}
    project_fields = core.utils.rest_api.get_sample_project_fields_data(project_name)
    if not project_fields or "ERROR" in project_fields:
        return {}
    display_map = {}
    for field in project_fields:
        field_name = field.get("sample_project_field_name")
        if not field_name:
            continue
        display_name = field.get("sample_project_field_description") or field.get(
            "sample_project_field_name"
        )
        display_map[field_name] = display_name
    return display_map


def analyze_input_samples(request):
    result = {}
    save_samples = []
    s_already_record = []
    s_incomplete = []
    s_json_data = json.loads(request.POST["table_data"])
    heading_in_form = request.POST["heading"].split(",")
    user_lab = (
        core.models.Profile.objects.filter(user=request.user).last().get_lab_name()
    )
    submmit_institution = core.utils.generic_functions.get_configuration_value(
        "SUBMITTING_INSTITUTION"
    )
    # Select the sample field that will be used in Sample class
    idx_sample = heading_in_form.index(core.config.FIELD_FOR_GETTING_SAMPLE_ID)
    allowed_empty_index = []
    for item in core.config.ALLOWED_EMPTY_FIELDS_IN_METADATA_SAMPLE_FORM:
        allowed_empty_index.append(heading_in_form.index(item))

    for row in s_json_data:
        row_data = {}
        incompleted = False
        sample_name = row[idx_sample]
        if sample_name == "":
            continue
        if core.models.core.models.Sample.objects.filter(
            sequencing_sample_id__iexact=sample_name
        ).exists():
            s_already_record.append(sample_name)
            continue
        for idx in range(len(heading_in_form)):
            if row[idx] == "" and idx not in allowed_empty_index:
                s_incomplete.append(row)
                incompleted = True
                break
            row_data[heading_in_form[idx]] = row[idx]
        if incompleted:
            break
        row_data["Originating Laboratory"] = user_lab
        row_data["Submitting Institution"] = submmit_institution
        save_samples.append(row_data)
    if len(save_samples) > 0:
        result["save_samples"] = save_samples
    if len(s_incomplete) > 0:
        result["s_incomplete"] = s_incomplete
    if len(s_already_record) > 0:
        result["s_already_record"] = s_already_record
    return result


def assign_samples_to_new_user(data):
    """Assign all samples from a laboratory to a new userID"""
    user_obj = User.objects.filter(pk__exact=data["userName"])
    if core.models.core.models.Sample.objects.filter(
        submitting_institution__iexact=data["lab"]
    ).exists():
        core.models.core.models.Sample.objects.filter(
            submitting_institution__iexact=data["lab"]
        ).update(user=user_obj[0])
        return {"Success": "Success"}
    return {
        "ERROR": core.config.ERROR_NO_SAMPLES_ARE_ASSIGNED_TO_LAB + " " + data["lab"]
    }


def count_handled_samples():
    """Count the number of samples handled in each process"""
    process = ["Defined", "Gisaid", "Ena", "Bioinfo"]
    counted_data = (
        core.models.DateUpdateState.objects.filter(stateID__state__in=process)
        .values("stateID__state")
        .annotate(count=Count("id"))
    )
    data = {entry["stateID__state"]: entry["count"] for entry in counted_data}
    # Replace Bioinfo count with the number of recorded analyses (one per run)
    bio_runs = core.models.BioinfoAnalysisValue.objects.filter(
        bioinfo_analysis_fieldID__property_name__iexact="bioinformatics_analysis_date",
        sample__isnull=False,
    ).count()
    data["Bioinfo"] = bio_runs
    # Ensure all expected keys exist so dashboards don't get missing dict entries
    for state in process:
        data.setdefault(state, 0)
    return data


def check_if_empty_data(data):
    """Check if user has not set any data in the form"""
    ignore_fields = ["csrfmiddlewaretoken", "action"]
    for key, value in data.items():
        if key in ignore_fields:
            continue
        if value != "":
            return True
    return False


def create_form_for_batch(schema_obj, user_obj):
    """Collect information for creating for batch from. This form is displayed
    only if previously was defined sample in sample form
    """
    schema_name = schema_obj.get_schema_name()
    try:
        iskylims_sample_raw = core.utils.rest_api.get_sample_fields_data()
    except AttributeError:
        return {"ERROR": core.config.ERROR_ISKYLIMS_NOT_REACHEABLE}
    if "ERROR" in iskylims_sample_raw:
        return iskylims_sample_raw
    # Remove the characters "schema" if exist in the name of the schema
    if "schema" in schema_name:
        schema_name = schema_name.replace("schema", "").strip()
    i_sam_proj_raw = core.utils.rest_api.get_sample_project_fields_data(schema_name)
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
    if not core.models.MetadataVisualization.objects.filter(
        fill_mode="sample"
    ).exists():
        return {"ERROR": core.config.ERROR_FIELDS_FOR_METADATA_ARE_NOT_DEFINED}
    m_batch_objs = core.models.MetadataVisualization.objects.filter(
        fill_mode="batch"
    ).order_by("order")

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
    m_batch_form["lab_name"] = core.utils.labs.get_lab_name_from_user(user_obj)

    return m_batch_form


def create_form_for_sample(schema_obj):
    """Collect information from iSkyLIMS and from metadata table to
    create the metadata form for filling sample data
    """
    m_form = OrderedDict()
    f_data = {}
    l_iskylims = []  # variable name in iSkyLIMS
    l_metadata = []  # label in the form
    if not core.models.MetadataVisualization.objects.filter(
        fill_mode="sample"
    ).exists():
        return {"ERROR": core.config.ERROR_FIELDS_FOR_METADATA_ARE_NOT_DEFINED}
    m_sam_objs = core.models.MetadataVisualization.objects.filter(
        fill_mode="sample"
    ).order_by("order")
    schema_name = schema_obj.get_schema_name()
    # Get the properties in schema for mapping
    s_prop_objs = core.models.SchemaProperties.objects.filter(schemaID=schema_obj)
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
        iskylims_sample_raw = core.utils.rest_api.get_sample_fields_data()
    except AttributeError:
        return {"ERROR": core.config.ERROR_ISKYLIMS_NOT_REACHEABLE}
    if "ERROR" in iskylims_sample_raw:
        return iskylims_sample_raw

    # Remove the characters "schema" if exist in the name of the schema
    if "schema" in schema_name:
        schema_name = schema_name.replace("schema", "").strip()
    i_sam_proj_raw = core.utils.rest_api.get_sample_project_fields_data(schema_name)
    if "ERROR" in i_sam_proj_raw:
        return {
            "ERROR": core.config.ERROR_UNABLE_FETCH_SAMPLE_PROJECT_FIELDS
            + "for "
            + schema_name
        }
    i_sam_proj_data = {}
    # Format the information from sample Project to have label as key
    # format of the field and the option list in aa list
    for item in i_sam_proj_raw:
        key = item["sample_project_field_description"]
        i_sam_proj_data[key] = {}
        i_sam_proj_data[key]["format"] = item["sample_project_field_type"]
        if item["sample_project_field_type"] == "Options List":
            i_sam_proj_data[key]["options"] = []
            for opt in item["sample_project_option_list"]:
                i_sam_proj_data[key]["options"].append(opt["option_value"])
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
    create the user metadata form
    """
    # Check if Fields for metadata Form are defiened
    if not core.models.MetadataVisualization.objects.exists():
        return {"ERROR": core.config.ERROR_FIELDS_FOR_METADATA_ARE_NOT_DEFINED}
    m_form = {}
    m_form["sample"] = create_form_for_sample(schema_obj)
    if "ERROR" in m_form["sample"]:
        return m_form["sample"]
    m_form["username"] = user_obj.username
    m_form["lab_name"] = core.utils.labs.get_lab_name_from_user(user_obj)
    return m_form


def create_date_sample_bar(lab_sample, cust_data):
    """Create bar graph where X-axis are the dates and Y-axis the number of
    samples. NOTE: Keep in mind that cust_data should already be ordered
    """
    df = pd.DataFrame(lab_sample.items(), columns=cust_data["col_names"])
    df[cust_data["col_names"][0]] = (
        df[cust_data["col_names"][0]]
        .astype(str)
        .str.replace(r"W(\d{1})$", r"W0\1", regex=True)
    )
    histogram = core.utils.plotly_graphics.histogram_graphic(
        df, cust_data["col_names"], cust_data["options"]
    )
    return histogram


def create_dash_bar_for_each_lab(labs_data, labs_list=None):
    """Create the Dash bar plot that compares the weekly reception per lab.

    Args:
        labs_data (Iterable[dict]): Entries containing at least
            ``lab_code_1`` (optional), ``collecting_institution`` (display name)
            and ``iso_yearweek`` + ``num_samples``.
        labs_list (Iterable[dict|str], optional): Option definitions for the
            dropdown. When omitted an option list is built from ``labs_data``.
    """

    df_data = pd.DataFrame(labs_data)
    if df_data.empty:
        return

    if "lab_code_1" not in df_data.columns:
        df_data["lab_code_1"] = None

    legacy_column = df_data.get("legacy_collecting_institution")
    if "collecting_institution" in df_data.columns:
        if legacy_column is not None:
            df_data["collecting_institution"] = df_data[
                "collecting_institution"
            ].fillna(legacy_column)
        else:
            df_data["collecting_institution"] = df_data[
                "collecting_institution"
            ].fillna("")
    else:
        if legacy_column is not None:
            df_data["collecting_institution"] = legacy_column.fillna("")
        else:
            df_data["collecting_institution"] = ""

    if labs_list is None:
        labs_list = []

    normalised_options = []
    seen_values = set()

    def _add_option(value, label):
        if not value or value in seen_values:
            return
        seen_values.add(value)
        normalised_options.append({"label": label or value, "value": value})

    for raw_option in labs_list:
        if isinstance(raw_option, dict):
            value = (
                raw_option.get("value")
                or raw_option.get("lab_code_1")
                or raw_option.get("collecting_institution")
                or raw_option.get("legacy_name")
            )
            label = (
                raw_option.get("label")
                or raw_option.get("collecting_institution")
                or raw_option.get("legacy_name")
                or raw_option.get("value")
                or raw_option.get("lab_code_1")
            )
        else:
            value = str(raw_option)
            label = value
        _add_option(value, label)

    if not normalised_options:
        for _, row in df_data.iterrows():
            code = row.get("lab_code_1")
            display = row.get("collecting_institution") or row.get(
                "legacy_collecting_institution"
            )
            value = code or display
            label = (
                core.utils.labs.get_display_name_from_code(code) if code else display
            )
            _add_option(value, label)

    core.utils.plotly_dash_graphics.dash_bar_lab(normalised_options, df_data)
    return


def fancy_gauge_graphic(value):
    return render_to_string("core/gauge_component.html", {"value": value})


def perc_gauge_graphic(values):
    data = {}
    if values["received"] == 0:
        data["value"] = 0
    else:
        x = values["analized"] / values["received"] * 100
        data["value"] = float("{:.2f}".format(x))
    gauge_graph = core.utils.plotly_graphics.gauge_graphic(data)
    return gauge_graph


def delete_temporary_sample_table(user_obj):
    """Set for all samples in the temporary table for the user that are sent
    to folder to start the process for validatation
    """
    if core.models.TemporalSampleStorage.objects.filter(user=user_obj).exists():
        core.models.TemporalSampleStorage.objects.filter(user=user_obj).delete()
    return True


def get_lab_last_actions(lab_name=None):
    """Get the last action performed on the samples for a specific lab.
    If no lab is given it returns the info for all labs
    """
    action_list = ["Defined", "Bioinfo", "Gisaid", "Ena"]
    if lab_name is None:
        lab_actions = []
        labs = core.models.core.models.Sample.objects.values_list(
            "submitting_institution"
        ).distinct()
        for lab in labs:
            sam_obj = core.models.core.models.Sample.objects.filter(
                submitting_institution__exact=lab[0]
            ).last()
            lab_data = [lab[0]]
            for action in action_list:
                if core.models.DateUpdateState.objects.filter(
                    sampleID=sam_obj, stateID__state__exact=action
                ).exists():
                    lab_data.append(
                        core.models.DateUpdateState.objects.filter(
                            sampleID=sam_obj, stateID__state__exact=action
                        )
                        .last()
                        .get_date()
                    )
                else:
                    lab_data.append("")
            lab_actions.append(lab_data)
        return lab_actions
    else:
        actions = {}
        last_sample_obj = core.models.core.models.Sample.objects.filter(
            submitting_institution__iexact=lab_name
        ).last()
        action_objs = core.models.DateUpdateState.objects.filter(
            sampleID=last_sample_obj
        )
        for action_obj in action_objs:
            s_state = action_obj.get_state_name()
            if s_state in action_list:
                actions[s_state] = action_obj.get_date()
        return actions


def get_gisaid_info(sample_obj, schema_obj):
    """Get the Gisaid information that is stored for the sample"""
    gisaid_info = []
    field_objs = get_public_database_fields(schema_obj, "gisaid")
    if field_objs is None:
        return gisaid_info
    for field_obj in field_objs:
        label = field_obj.get_label_name()
        value = ""
        gisaid_fields = core.models.PublicDatabaseValues.objects.filter(
            public_database_fieldID=field_obj, sampleID=sample_obj
        )
        if gisaid_fields.exists():
            value = gisaid_fields.last().get_value()
        gisaid_info.append([label, value])
    return gisaid_info


def get_public_database_fields(schema_obj, db_type):
    """Return the fields allocated for databse type"""
    if core.models.PublicDatabaseFields.objects.filter(
        schemaID=schema_obj, database_type__public_type_name__iexact=db_type
    ).exists():
        return core.models.PublicDatabaseFields.objects.filter(
            schemaID=schema_obj, database_type__public_type_name__iexact=db_type
        )
    return None


def get_sample_display_data(sample_id, user):
    """Check if user is allowed to see the data and if true collect all info
    from sample to display
    """
    sample_obj = get_sample_obj_from_id(sample_id)
    if sample_obj is None:
        return {"ERROR": core.config.ERROR_SAMPLE_DOES_NOT_EXIST}
    # Allow to see information obut sample to relecovManager
    manager_group = Group.objects.get(name="RelecovManager")
    if manager_group not in user.groups.all():
        user_role = core.utils.generic_functions.get_user_role(user)
        user_inst_field = core.utils.generic_functions.get_user_lab_field(user)
        user_lab_name = core.utils.labs.get_lab_name_from_user(user)

        if user_role == "Collector":
            allowed_codes = set(core.utils.labs.get_lab_codes_from_user(user))
            sample_code = getattr(sample_obj, "lab_code_1", None)
            sample_lab_name = getattr(sample_obj, "collecting_institution", "")
            if sample_code in allowed_codes:
                pass
            elif (
                user_lab_name
                and sample_lab_name
                and sample_lab_name.lower() == user_lab_name.lower()
            ):
                pass
            else:
                return {"ERROR": core.config.ERROR_NOT_ALLOWED_TO_SEE_THE_SAMPLE}
        else:
            sample_lab = getattr(sample_obj, user_inst_field, None)
            if (
                not sample_lab
                or not user_lab_name
                or sample_lab.lower() != user_lab_name.lower()
            ):
                return {"ERROR": core.config.ERROR_NOT_ALLOWED_TO_SEE_THE_SAMPLE}

    s_data = {}
    s_data["sample_name"] = sample_obj.get_sample_name()
    s_data["basic"] = list(
        zip(
            core.config.HEADING_FOR_BASIC_SAMPLE_DATA,
            sample_obj.get_sample_basic_data(),
        )
    )
    s_data["fastq"] = list(
        zip(
            core.config.HEADING_FOR_FASTQ_SAMPLE_DATA,
            sample_obj.get_fastq_data(),
        )
    )
    # Fetch actions done on the sample
    if core.models.DateUpdateState.objects.filter(sampleID=sample_obj).exists():
        actions = []
        actions_date_objs = core.models.DateUpdateState.objects.filter(
            sampleID=sample_obj
        ).order_by("-date")
        for action_date_obj in actions_date_objs:
            actions.append(
                [action_date_obj.get_state_display_name(), action_date_obj.get_date()]
            )
        s_data["actions"] = actions

    # Lab metadata in iSkyLIMS is keyed by the platform-wide unique sample id
    # (the value shown as Sample Name in iSky). Keep a fallback to the historical
    # sequencing_sample_id so legacy records can still resolve.
    lookup_ids = []
    unique_id = (sample_obj.get_unique_id() or "").strip()
    seq_id = (sample_obj.get_sequencing_sample_id() or "").strip()
    if unique_id:
        lookup_ids.append(unique_id)
    if seq_id and seq_id not in lookup_ids:
        lookup_ids.append(seq_id)

    # Fetch information from iSkyLIMS
    for sample_id in lookup_ids:
        iskylims_data = core.utils.rest_api.get_sample_information(sample_id)
        if not iskylims_data or "ERROR" in iskylims_data:
            continue
        s_data["iskylims_basic"] = []
        s_data["iskylims_p_data"] = []
        # iskylims_data is a list with one element. Then get the first element
        iskylims_data = iskylims_data[0]
        project_field_display_map = get_iskylims_project_field_display_map(
            iskylims_data.get("sample_project")
        )
        for key, i_data in iskylims_data.items():
            if key == "Project values":
                for p_key, p_data in iskylims_data["Project values"].items():
                    s_data["iskylims_p_data"].append(
                        [
                            project_field_display_map.get(p_key, p_key),
                            p_data,
                        ]
                    )
            else:
                s_data["iskylims_basic"].append([key, i_data])
        s_data["iskylims_project"] = iskylims_data.get("sample_project")
        break
    return s_data


def get_sample_obj_from_sample_name(sample_name):
    """Return the sample instance from its name"""
    if core.models.Sample.objects.filter(
        sequencing_sample_id__iexact=sample_name
    ).exists():
        return core.models.Sample.objects.filter(
            sequencing_sample_id__iexact=sample_name
        ).last()
    return None


def get_sample_obj_from_unique_sample_id(unique_sample_id):
    """Return the Sample instance from its unique, persisted identifier (sample_unique_id)."""
    qs = core.models.Sample.objects.filter(sample_unique_id__iexact=unique_sample_id)
    return qs.last() if qs.exists() else None


def get_sample_obj_from_fingerprint(sample_fingerprint):
    """Return the sample instance from its unique fingerprint"""
    if core.models.Sample.objects.filter(
        sample_fingerprint__iexact=sample_fingerprint
    ).exists():
        return core.models.Sample.objects.filter(
            sample_fingerprint__iexact=sample_fingerprint
        ).last()
    return None


def get_sample_obj_from_id(sample_id):
    """Return the sample instance from its id"""
    if core.models.Sample.objects.filter(pk__exact=sample_id).exists():
        return core.models.Sample.objects.filter(pk__exact=sample_id).last()
    return None


def get_samples_count_per_schema(schema_obj):
    """Get the number of samples that are stored in the schema"""
    return core.models.Sample.objects.filter(schema_obj=schema_obj).count()


def get_samples_count():
    """
    Total number of samples in the Sample table (all schemas).
    """
    return core.models.Sample.objects.count()


def get_sample_per_date_per_all_lab(detailed=None):
    """Get the historic of submitted sample for all labs. Merging the number
    of samples if they are in the same date. Function creates a dictionary
    with dates and number of samples if detailed is true return a
    """
    if detailed is None:
        all_samples_per_date = (
            dashboard.utils.generic_graphic_data.get_graphic_json_data(
                "samples_per_date_all_lab"
            )
        )
        if all_samples_per_date is None:
            # Execute the pre-processed task to get the data
            result = (
                dashboard.utils.generic_process_data.pre_proc_samples_per_date_all_lab()
            )
            if "ERROR" in result:
                return result
            all_samples_per_date = (
                dashboard.utils.generic_graphic_data.get_graphic_json_data(
                    "samples_per_date_all_lab"
                )
            )
        return all_samples_per_date
    else:
        lab_date_count = dashboard.utils.generic_graphic_data.get_graphic_json_data(
            "samples_per_date_all_lab_detailed"
        )
        if lab_date_count is None:
            # Execute the pre-processed task to get the data
            result = (
                dashboard.utils.generic_process_data.pre_proc_samples_per_date_all_lab(
                    detailed=True
                )
            )
            if "ERROR" in result:
                return result
            lab_date_count = dashboard.utils.generic_graphic_data.get_graphic_json_data(
                "samples_per_date_all_lab_detailed"
            )
        return lab_date_count


def get_search_table_for_user(user_obj):
    """Extract the data to fill the table of available samples to search
    for the given user, prioritizing lab_code_1 when available"""
    samples_to_search = dashboard.utils.generic_graphic_data.get_graphic_json_data(
        "search_samples_summary_table"
    )
    if samples_to_search is None:
        # Execute the pre-processed task to get the data
        result = dashboard.utils.generic_process_data.pre_proc_search_samples_summary()
        if "ERROR" in result:
            return result
        samples_to_search = dashboard.utils.generic_graphic_data.get_graphic_json_data(
            "search_samples_summary_table"
        )
    user_role = core.utils.generic_functions.get_user_role(user_obj)
    table_data = []
    if user_role == "RelecovManager":
        for subinst_labs_dict in samples_to_search.values():
            for info in subinst_labs_dict.values():
                table_data.extend(info.get("rows", []))
        return table_data
    if user_role == "Submitter":
        user_lab = core.utils.labs.get_lab_name_from_user(user_obj)
        lab_entries = samples_to_search.get(user_lab, {})
        for info in lab_entries.values():
            table_data.extend(info.get("rows", []))
    else:
        lab_codes = set(core.utils.labs.get_lab_codes_from_user(user_obj))
        user_lab = core.utils.labs.get_lab_name_from_user(user_obj)
        for subinst_labs_dict in samples_to_search.values():
            for info in subinst_labs_dict.values():
                bucket_code = info.get("lab_code_1")
                bucket_display = info.get("collecting_institution")
                rows = info.get("rows", [])
                matched = False
                if lab_codes and bucket_code and bucket_code in lab_codes:
                    matched = True
                elif (
                    (not lab_codes or not bucket_code)
                    and user_lab
                    and bucket_display
                    and bucket_display.lower() == user_lab.lower()
                ):
                    matched = True
                if matched:
                    table_data.extend(rows)
    if not table_data:
        print(f"Found no sample for user {user_obj.username} in search_samples_summary")
    return table_data


# FIXME: If no lab name is assigned to the user, display a custom error screen.
#        The error occurs when lab_name is 'None' after accessing to intranet.
def get_sample_per_date_per_lab(lab_name):
    """Get the historic of submitted sample, creating a dictionary with dates
    and number of samples
    """
    samples_per_date = OrderedDict()

    s_dates = (
        core.models.Sample.objects.filter(submitting_institution__iexact=lab_name)
        .values_list("collecting_date", flat=True)
        .distinct()
        .order_by("collecting_date")
    )
    for s_date in s_dates:
        date = datetime.strftime(s_date, "%Y-W%V")
        samples_per_date[date] = core.models.Sample.objects.filter(
            submitting_institution__iexact=lab_name, collecting_date=s_date
        ).count()
    return samples_per_date


def get_sample_objs_per_lab(lab_name):
    """Get all sample instance for the lab who the user is responsible"""
    return core.models.Sample.objects.filter(submitting_institution__iexact=lab_name)


def get_user_id_from_submitting_institution(lab):
    """Use the laboratory name defined in the Profile (submitting-institution)
    to find out the user. if no user is not defined with this lab it returns None
    """
    if core.models.Profile.objects.filter(laboratory__iexact=lab).exists():
        return core.models.Profile.objects.filter(laboratory__iexact=lab).last().user.pk
    return None


def join_sample_and_batch(b_data, user_obj, schema_obj):
    """Get the sample information stored on temporary tables and join with the
    batch data.
    """
    join_data = []
    sample_dict = {}
    if not core.models.TemporalSampleStorage.objects.filter(user=user_obj).exists():
        return {"ERROR": core.config.ERROR_SAMPLES_NOT_DEFINED_IN_FORM}
    field_list = list(
        core.models.MetadataVisualization.objects.filter(schemaID=schema_obj)
        .order_by("order")
        .values_list("label_name", flat=True)
    )
    join_data.append(field_list)
    t_sample_objs = core.models.TemporalSampleStorage.objects.filter(user=user_obj)
    for t_sample_obj in t_sample_objs:
        s_name = t_sample_obj.get_sample_name()
        if s_name not in sample_dict:
            sample_dict[s_name] = {}
        sample_dict[s_name].update(t_sample_obj.get_temp_values())

    for key in sample_dict.keys():
        row_data = []
        for field_name in field_list:
            if field_name in b_data:
                row_data.append(b_data[field_name])
            elif field_name in sample_dict[key]:
                row_data.append(sample_dict[key][field_name])
            else:
                print("error not defined", field_name, " for sample ", key)
                row_data.append("")
        join_data.append(row_data)

    return join_data


def get_all_submitting_insts():
    """Function to get all lab/submitting_institutions in an ordered list"""
    return list(
        core.models.Sample.objects.values_list("submitting_institution", flat=True)
        .distinct()
        .order_by("submitting_institution")
    )


def get_all_collecting_insts():
    """Return the list of collecting institutions mapped to their lab codes."""

    records = (
        core.models.Sample.objects.order_by()
        .values("lab_code_1", "collecting_institution")
        .distinct()
    )

    options = []
    seen_values = set()
    for entry in records:
        lab_code = entry.get("lab_code_1")
        legacy_name = entry.get("collecting_institution")
        value = lab_code or legacy_name
        if not value or value in seen_values:
            continue
        label = core.utils.labs.get_display_name_from_code(lab_code)
        if not label:
            label = legacy_name or value
        options.append(
            {
                "value": value,
                "label": label,
                "lab_code_1": lab_code,
                "legacy_name": legacy_name,
            }
        )
        seen_values.add(value)
    return options


def get_all_recieved_samples_with_dates(accumulated=False):
    """Get all samples that are received in the platform. If accumulated is
    True then functions return the value of the date the sum of the predecesor
    values. If False just the value received for each date
    """
    r_samples = []
    if not core.models.Sample.objects.exists():
        return r_samples
    date_counts = (
        core.models.Sample.objects.annotate(date_only=TruncDate("created_at"))
        .values("date_only")
        .annotate(count=Count("id"))
        .order_by("date_only")
    )
    sum = 0
    for date_count in date_counts:
        s_date = date_count["date_only"]
        value = date_count["count"]

        if accumulated:
            sum += value
            r_samples.append({s_date: sum})
        else:
            r_samples.append({s_date: value})

    return r_samples


def get_sample_pre_recorded(user_obj):
    """Function returns a list of the samples that are pending to add the
    batch information for those samples
    """
    return list(
        core.models.TemporalSampleStorage.objects.filter(
            user=user_obj, field__exact="Sample ID given for sequencing"
        ).values_list("value", flat=True)
    )


def increase_unique_value(old_unique_number):
    """The function increases in one number the unique value
    If number reaches the 9999 then the letter is stepped
    """
    split_value = old_unique_number.split("-")
    number = int(split_value[2]) + 1
    letter = split_value[1]

    if number > 9999:
        number = 1
        index_letter = list(split_value[1])
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
    return str(core.config.SAMPLE_ID_PREFIX + letter + "-" + number_str)


def pending_samples_in_metadata_form(user_obj):
    """Check if there are samples waiting to be completed for the metadata form"""
    if core.models.TemporalSampleStorage.objects.filter(user=user_obj).exists():
        return True
    return False


def save_excel_form_in_samba_folder(m_file, user_name):
    f_name = user_name + "_" + m_file.name
    f_path = os.path.join(
        core.utils.generic_functions.get_configuration_value("SAMBA_FOLDER"),
        f_name,
    )
    """Save the metadata lab file in Samba folder"""
    FileSystemStorage().save(f_name, m_file)
    # moving file
    shutil.move(os.path.join(settings.MEDIA_ROOT, f_name), f_path)
    return


def search_samples(sample_name, lab_name, sample_state, s_date, user):
    """Search the samples that match with the query conditions"""
    sample_list = []
    sample_objs = get_available_samples_for_user(user)
    if s_date != "":
        samples_with_coldate = core.utils.rest_api.fetch_samples_on_condition(
            "collection_sample_date"
        )
        dates_samples_dict = defaultdict(list)
        if "ERROR" in samples_with_coldate:
            return samples_with_coldate
        for d in samples_with_coldate["DATA"]:
            dates_samples_dict[d["collection_sample_date"]].append(d["Sample Name"])
        sample_objs = core.models.Sample.objects.filter(
            Q(sequencing_sample_id__in=dates_samples_dict.get(s_date, []))
            | Q(collecting_lab_sample_id__iexact=dates_samples_dict.get(s_date, []))
        )
    if lab_name != "":
        sample_objs = sample_objs.filter(collecting_institution__iexact=lab_name)
    if sample_name != "":
        if sample_objs.filter(
            Q(sequencing_sample_id__iexact=sample_name)
            | Q(collecting_lab_sample_id__iexact=sample_name)
        ).exists():
            sample_objs = sample_objs.filter(
                Q(sequencing_sample_id__iexact=sample_name)
                | Q(collecting_lab_sample_id__iexact=sample_name)
            )
            if len(sample_objs) == 1:
                sample_list.append(sample_objs[0].get_sample_id())
                return sample_list

        elif sample_objs.filter(
            Q(sequencing_sample_id__icontains=sample_name)
            | Q(collecting_lab_sample_id__icontains=sample_name)
        ).exists():
            sample_objs = sample_objs.filter(
                Q(sequencing_sample_id__icontains=sample_name)
                | Q(collecting_lab_sample_id__icontains=sample_name)
            )
            if len(sample_objs) == 1:
                sample_list.append(sample_objs[0].get_sample_id())
                return sample_list
        else:
            return sample_list
    if sample_state != "":
        state_ids = list(
            core.models.DateUpdateState.objects.filter(
                stateID__pk__exact=sample_state
            ).values_list("sampleID__pk", flat=True)
        )
        sample_objs = sample_objs.filter(pk__in=state_ids)
    if len(sample_objs) == 1:
        sample_list.append(sample_objs[0].get_sample_id())
        return sample_list
    for sample_obj in sample_objs:
        sample_list.append(sample_obj.get_info_for_searching())
    return sample_list


def get_available_samples_for_user(user_obj):
    """Return the samples that the user should be able to see,
    wether its a Manager, Submitter or Collector. Based on its laboratory"""
    user_role = core.utils.generic_functions.get_user_role(user_obj)
    profile_obj = core.models.Profile.objects.filter(user=user_obj).last()
    user_lab = profile_obj.get_lab_name() if profile_obj else ""
    if user_role == "RelecovManager":
        return core.models.Sample.objects.all()
    elif user_role == "Submitter":
        return core.models.Sample.objects.filter(
            submitting_institution__iexact=user_lab
        )
    elif user_role == "Collector":
        lab_codes = core.utils.labs.get_lab_codes_from_user(user_obj)
        filters = Q()
        if lab_codes:
            filters |= Q(lab_code_1__in=lab_codes)
        if user_lab:
            filters |= Q(collecting_institution__iexact=user_lab)
        if not filters.children:
            return core.models.Sample.objects.none()
        return core.models.Sample.objects.filter(filters).distinct()
    else:
        return core.models.Sample.objects.none()


def save_temp_sample_data(samples, user_obj):
    """Store the valid sample into the temporary table"""
    sample_saved_list = []
    for sample in samples:
        for item, value in sample.items():
            """
            TODO: This needs special handling to implement sample_fingerprint.
            This data is used to create a temporal table during metadata form completion.
            Changing core.config.FIELD_FOR_GETTING_SAMPLE_ID would imply that the user needs to know
            the sample_fingerprint, which is impossible. But at the same time its needed to ensure uniqueness.
            """
            data = {"sample_name": sample[core.config.FIELD_FOR_GETTING_SAMPLE_ID]}
            data["field"] = item
            data["value"] = value
            data["user"] = user_obj
            core.models.TemporalSampleStorage.objects.save_temp_data(data)
        # Include Originating Laboratory and Submitting Institution

        sample_saved_list.append(sample[core.config.FIELD_FOR_GETTING_SAMPLE_ID])
    return


def write_form_data_to_excel(data, user_obj):
    """Write data to excel using relecov-tools"""
    samba_folder = core.utils.generic_functions.get_configuration_value("SAMBA_FOLDER")
    os.makedirs(samba_folder, exist_ok=True)
    f_name = os.path.join(samba_folder, "Metadata_lab_" + user_obj.username + ".xlsx")
    relecov_tools.utils.write_to_excel_file(data, f_name, "METADATA_LAB", {})
    return


def build_sample_fingerprint(seq_id, colect_id, submit_inst, colect_inst):
    """Return the expected sample fingerprint given its 4 components"""
    combined = f"{seq_id}|{colect_id}|{submit_inst}|{colect_inst}".lower()
    return hashlib.sha256(combined.encode()).hexdigest()[:24]
