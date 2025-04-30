from django.db.models import Count, Q, Max, OuterRef, Subquery
from django.contrib.auth.models import Group
from django.db.models.functions import TruncDate
from collections import OrderedDict

import core.models
import core.serializers
import core.config
import core.utils.utils
import core.utils.rest_api
import core.utils
import core.utils.variants

# TODO: Some functions are still being called from utils.py. 
# Move those functions into proper service modules and import them accordingly. 
# Keep utils.py only for generic utilities (e.g., data processing, conversions, etc.).
# TODO: add docsrings and sort functions.
# TODO: There are several functions in utils* that have been reimplemented here. Clean them to avoid duplicates

# util
def get_configuration_value(parameter_name):
    """Get a value from the configuration model."""
    return (
        core.models.ConfigSetting.objects
        .filter(configuration_name=parameter_name)
        .values_list("configuration_value", flat=True)
        .last()
    ) or "False"

# util
def get_sample_count_qs():
    """Count number of samples by state."""
    return (
        core.models.SampleStateHistory.objects
        .values("state_id__state")
        .annotate(count=Count("id"))
    )

# service
def get_index_data():
    result = {"data":{}, "success":False, "errors":[]}

    # Get sample counts by state and serialize data
    try:
        sample_count_qs = get_sample_count_qs()
        serialized = core.serializers.SampleCountByStateSerializer(sample_count_qs, many=True).data
        # Transform data structur
        result["data"]["number_of_samples"] = {entry["label"]: entry["count"] for entry in serialized}
    except Exception as e:
        result["errors"].append({"code": 500, "message": f"Error loading sample counts: {str(e)}"})

    # Get Nextrain configuration
    try:
        result["data"]["nextstrain_url"] = get_configuration_value("NEXTSTRAIN_URL")
    except Exception as e:
        result["errors"].append({"code": 500, "message": f"Error loading Nextstrain URL: {str(e)}"})

    # Return success
    result["success"] = len(result["errors"]) == 0
    return result


def get_labs_and_users_data():
    labs = get_all_defined_labs()
    users = get_defined_users()
    return core.serializers.LabUserAssignSerializer.from_raw_data(
        labs=labs,
        users=users,
    )

def get_sample_obj_from_id(sample_id):
    """Return the sample instance from its id"""
    if core.models.Sample.objects.filter(pk__exact=sample_id).exists():
        return core.models.Sample.objects.filter(pk__exact=sample_id).last()
    return None

def assign_samples_to_user_by_lab(lab, user_id):
    labs = get_all_defined_labs()
    users = get_defined_users()
    if not user_id:
        return core.serializers.LabUserAssignSerializer.from_raw_data(
            labs=labs,
            users=users,
            ERROR="No user selected. Please choose a user before submitting."
        )

    try:
        user_obj = core.models.User.objects.get(pk=user_id)
    except core.models.User.DoesNotExist:
        return core.serializers.LabUserAssignSerializer.from_raw_data(
            labs=labs,
            users=users,
            ERROR=f"User with ID {user_id} does not exist."
        )

    samples_qs = core.models.Sample.objects.filter(collecting_institution__iexact=lab)
    if samples_qs.exists():
        samples_qs.update(user=user_obj)
        return core.serializers.LabUserAssignSerializer.from_raw_data(
            labs=labs,
            users=users,
            SUCCESS="Samples successfully reassigned."
        )

    return core.serializers.LabUserAssignSerializer.from_raw_data(
        labs=labs,
        users=users,
        ERROR=f"{core.config.ERROR_NO_SAMPLES_ARE_ASSIGNED_TO_LAB} {lab}"
    )


def get_all_defined_labs():
    """Get a list of laboratories that are defined in iSkyLIMS"""
    sum_data = core.utils.rest_api.get_summarize_data(None)
    if "ERROR" in sum_data:
        return sum_data
    return list(sum_data["laboratory"].keys())


def get_defined_users():
    """Get the id and the user names defined in relecov"""
    user_list = []
    user_objs = (
        core.models.User.objects.all().exclude(username__iexact="admin").order_by("username")
    )
    for user_obj in user_objs:
        user_list.append([user_obj.pk, user_obj.username])
    return user_list


def get_labs_and_users():
    """Prepares data for sample allocation form."""
    raw_data = {
        "labs": get_all_defined_labs(),
        "users": get_defined_users()
    }
    return core.serializers.LabUserDataSerializer.from_raw_data(raw_data)

def get_lab_name_from_user(user_obj):
    """Get the laboratory name for the user"""
    if core.models.Profile.objects.filter(user=user_obj).exists():
        profile_obj = core.models.Profile.objects.filter(user=user_obj).last()
        return profile_obj.get_lab_name()
    else:
        return ""


# FIXME: refactor its output
def get_search_data(user_obj):
    """Structure data to render form in search sample view."""
    if core.models.Sample.objects.count() == 0:
        return {"ERROR": core.config.ERROR_NOT_SAMPLES_HAVE_BEEN_DEFINED}

    # Serialize available states request
    states_qs = core.models.SampleState.objects.all()
    serialized_states = core.serializers.SampleStateSerializer(states_qs, many=True).data

    # Get laboratories available in the user's group
    group = Group.objects.get(name="RelecovManager")
    if group in user_obj.groups.all():
        labs = get_all_defined_labs()
        if isinstance(labs, dict) and "ERROR" in labs:
            labs = ["", ""]
    else:
        labs = [get_lab_name_from_user(user_obj)]

    return {
        "labs": labs,
        "states": serialized_states,
    }

# FIXME: refactor its output 
def display_samples(sample_name, lab_name, sample_state, s_date, user):
    """Sample filtering according to params and return structured, serialized data."""

    sample_objs = core.models.Sample.objects.all()

    if lab_name:
        sample_objs = sample_objs.filter(collecting_institution__iexact=lab_name)

    if sample_name:
        exact_qs = sample_objs.filter(
            Q(sequencing_sample_id__iexact=sample_name)
            | Q(collecting_lab_sample_id__iexact=sample_name)
        )
        if exact_qs.exists():
            sample_objs = exact_qs
        else:
            partial_qs = sample_objs.filter(
                Q(sequencing_sample_id__icontains=sample_name)
                | Q(collecting_lab_sample_id__icontains=sample_name)
            )
            if partial_qs.exists():
                sample_objs = partial_qs
            else:
                return {
                    "list_display": {
                        "s_data": [],
                        "heading": core.config.HEADING_FOR_SAMPLE_LIST,
                        "redirect": None,
                        "ERROR": core.config.ERROR_NOT_MATCHED_ITEMS_IN_SEARCH
                    }
                }

    if sample_state:
        sample_ids = core.models.SampleStateHistory.objects.filter(
            state_id__pk=sample_state
        ).values_list("sample__pk", flat=True)
        sample_objs = sample_objs.filter(pk__in=sample_ids)

    if s_date:
        sample_objs = sample_objs.filter(created_at__exact=s_date)

    if not sample_objs.exists():
        return {
            "list_display": {
                "s_data": [],
                "heading": core.config.HEADING_FOR_SAMPLE_LIST,
                "redirect": None,
                "ERROR": core.config.ERROR_NOT_MATCHED_ITEMS_IN_SEARCH
            }
        }

    if sample_objs.count() == 1:
        return {
            "list_display": {
                "s_data": [],
                "heading": core.config.HEADING_FOR_SAMPLE_LIST,
                "redirect": sample_objs.first().pk,
                "ERROR": None
            }
        }

    serialized_samples = core.serializers.SampleSearchResultSerializer(sample_objs, many=True).data

    return {
        "list_display": {
            "s_data": serialized_samples,
            "heading": core.config.HEADING_FOR_SAMPLE_LIST,
            "redirect": None,
            "ERROR": None
        }
    }


# FIXME: refactor its output
def get_sample_per_date_per_all_lab(detailed=False):
    """
    Return number of samples per sequencing date (grouped by date).
    
    - If `detailed` is False (default), return global counts (date -> count).
    - If `detailed` is True, return per-lab counts: [{"lab_name": ..., "date": ..., "num_samples": ...}, ...]
    """
    if not detailed:
        samples_by_date = (
            core.models.Sample.objects
            #.exclude(sequencing_date__isnull=True)
            .annotate(date_only=TruncDate("sequencing_date"))
            .values("date_only")
            .annotate(count=Count("id"))
            .order_by("date_only")
        )

        result = OrderedDict()
        for entry in samples_by_date:
            formatted_date = entry["date_only"].strftime("%d-%B-%Y")
            result[formatted_date] = entry["count"]
        return result

    else:
        samples_by_lab_and_date = (
            core.models.Sample.objects
            .exclude(sequencing_date__isnull=True)
            .annotate(date_only=TruncDate("sequencing_date"))
            .values("collecting_institution", "date_only")
            .annotate(count=Count("id"))
            .order_by("collecting_institution", "date_only")
        )

        result = []
        for entry in samples_by_lab_and_date:
            result.append({
                "lab_name": entry["collecting_institution"],
                "date": entry["date_only"].strftime("%d-%B-%Y"),
                "num_samples": entry["count"]
            })
        return result


# FIXME: refactor its output
def get_intranet_data_for_manager():
    all_sample_per_date = core.utils.samples.get_sample_per_date_per_all_lab()
    num_of_samples = core.utils.samples.count_handled_samples()
    analysis_percent = core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab()

    bar_config = {
        "col_names": ["Sequencing Date", "Number of samples"],
        "options": {
            "title": "Samples Received for all laboratories",
            "width": 590,
        },
    }

    # dash graph for samples per lab
    core.utils.samples.create_dash_bar_for_each_lab()
    
    # Collect data that populate views
    gisaid_raw = core.utils.public_db.get_public_accession_from_sample_lab("gisaid_accession_id")
    ena_raw = core.utils.public_db.get_public_accession_from_sample_lab("ena_sample_accession")
    actions_raw = core.utils.samples.get_lab_last_actions()
    data = {
        "sample_bar_graph": core.utils.samples.create_date_sample_bar(all_sample_per_date, bar_config),
        "sample_gauge_graph": core.utils.utils.perc_gauge_graphic(analysis_percent),
        "actions": core.serializers.LabLastActionSerializer.from_raw(actions_raw),
    }

    if gisaid_raw:
        data["gisaid_accession"] = core.serializers.PublicAccessionSerializer.from_raw(gisaid_raw)
        data["gisaid_graph"] = core.utils.public_db.percentage_graphic(
            num_of_samples.get("Defined", 0), len(gisaid_raw), ""
        )

    if ena_raw:
        data["ena_accession"] = core.serializers.PublicAccessionSerializer.from_raw(ena_raw)
        data["ena_graph"] = core.utils.public_db.percentage_graphic(
            num_of_samples.get("Defined", 0), len(ena_raw), ""
        )

    return data


# FIXME: refactor its output

def get_intranet_data_for_user(user):
    lab_name = get_lab_name_from_user(user)
    date_lab_samples = core.utils.samples.get_sample_per_date_per_lab(lab_name)

    if not date_lab_samples:
        return f"No samples found for selected laboratory: {lab_name}"

    sample_lab_objs = core.utils.samples.get_sample_objs_per_lab(lab_name)
    analysis_percent = core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab(lab_name)

    bar_config = {
        "col_names": ["Sequencing Date", "Number of samples"],
        "options": {
            "title": "Samples Received",
            "width": 600,
        },
    }

    gisaid_raw = core.utils.public_db.get_public_accession_from_sample_lab("gisaid_accession_id", sample_lab_objs)
    ena_raw = core.utils.public_db.get_public_accession_from_sample_lab("ena_sample_accession", sample_lab_objs)
    actions_raw = core.utils.samples.get_lab_last_actions(lab_name)

    intra_data = {
        "sample_bar_graph": core.utils.samples.create_date_sample_bar(date_lab_samples, bar_config),
        "sample_gauge_graph": core.utils.utils.perc_gauge_graphic(analysis_percent),
        "actions": core.serializers.LabLastActionDictSerializer.from_raw(actions_raw),
    }

    if gisaid_raw:
        intra_data["gisaid_accession"] = core.serializers.PublicAccessionSerializer.from_raw(gisaid_raw)
        intra_data["gisaid_graph"] = core.utils.public_db.percentage_graphic(
            len(sample_lab_objs), len(gisaid_raw), ""
        )

    if ena_raw:
        intra_data["ena_accession"] = core.serializers.PublicAccessionSerializer.from_raw(ena_raw)
        intra_data["ena_graph"] = core.utils.public_db.percentage_graphic(
            len(sample_lab_objs), len(ena_raw), ""
        )

    return intra_data

def get_actions_qs(sample_obj):
    try:
        actions_qs = core.models.SampleStateHistory.objects.filter(sample=sample_obj).order_by("-changed_at")
        return actions_qs, None
    except Exception as e:
        return [], {"code": 500, "message": f"Error fetching actions: {str(e)}"}

def get_public_db_qs(sample_obj, db_name):
    try:
        qs = core.models.PublicDatabaseValues.objects.filter(
            sampleID=sample_obj,
            public_database_fieldID__database_type__public_type_name__iexact=db_name
        )
        return qs, None
    except Exception as e:
        return [], {"code": 500, "message": f"Error fetching public DB '{db_name}': {str(e)}"}


def get_bioinfo_qs(sample_obj):
    try:
        schema_obj = sample_obj.get_schema_obj()
        if not schema_obj:
            return [], {"code": 404, "message": "Schema not found for sample"}

        bioan_fields_qs = core.models.MetadataValues.objects.filter(
            schema_property__schemaID=schema_obj,
            sample=sample_obj,
        )
        latest_analysis_date = bioan_fields_qs.aggregate(Max("analysis_date"))["analysis_date__max"]
        if not latest_analysis_date:
            return [], {"code": 404, "message": "No bioinformatics analysis date found"}

        filtered_qs = bioan_fields_qs.filter(
            analysis_date=latest_analysis_date,
            generated_at=Subquery(
                bioan_fields_qs.filter(
                    analysis_date=latest_analysis_date,
                    schema_property=OuterRef("schema_property"),
                    value=OuterRef("value"),
                ).order_by("-generated_at").values("generated_at")[:1]
            )
        )
        return filtered_qs, None
    except Exception as e:
        return [], {"code": 500, "message": f"Error fetching bioinfo data: {str(e)}"}


def get_lineage_qs(sample_obj):
    try:
        schema_obj = sample_obj.get_schema_obj()
        if not schema_obj:
            return [], {"code": 404, "message": "Schema not found for sample"}

        lineage_fields = core.models.LineageFields.objects.filter(schemaID=schema_obj)
        lineage_qs = []
        for field in lineage_fields:
            value_qs = core.models.LineageValues.objects.filter(
                lineage_fieldID=field, sample=sample_obj
            ).order_by("-generated_at")
            if value_qs.exists():
                lineage_qs.append(value_qs.first())

        return lineage_qs, None
    except Exception as e:
        return [], {"code": 500, "message": f"Error fetching lineage data: {str(e)}"}


def get_variant_and_graphic_data(sample_id):
    variant_data = {}
    graphic_data = None
    try:
        # Load variant data
        variant_data = core.utils.variants.get_variant_qs(sample_id)
        if "heading" in variant_data:
            graphic_data = core.utils.variants.get_variant_graphic_from_sample(sample_id)
    except Exception as e:
        return None, None, {"code": 500, "message": f"Error getting variant data: {str(e)}"}
    return variant_data, graphic_data, None


def get_sample_display_data(sample_id, user):
    result = {"data": {}, "success": False, "errors": []}

    # Validate sample
    sample_obj = get_sample_obj_from_id(sample_id)
    if not sample_obj:
        result["errors"].append({"code": 404, "message": core.config.ERROR_SAMPLE_DOES_NOT_EXIST})
        return result

    # Check by group permissions
    group = Group.objects.get(name="RelecovManager")
    if group not in user.groups.all():
        lab_name = sample_obj.get_collecting_institution()
        if not core.models.Profile.objects.filter(user=user, laboratory__iexact=lab_name).exists():
            result["errors"].append({"code": 403, "message": core.config.ERROR_NOT_ALLOWED_TO_SEE_THE_SAMPLE})
            return result

    # Recover error handling
    actions_qs, err = get_actions_qs(sample_obj)
    if err:
        result["errors"].append(err)

    gisaid_qs, err = get_public_db_qs(sample_obj, "gisaid")
    if err:
        result["errors"].append(err)

    ena_qs, err = get_public_db_qs(sample_obj, "ena")
    if err:
        result["errors"].append(err)

    bioinfo_qs, err = get_bioinfo_qs(sample_obj)
    if err: 
        result["errors"].append(err)

    lineage_qs, err = get_lineage_qs(sample_obj)
    if err:
        result["errors"].append(err)

    # Generate variant data
    variant_data, graphic_data, variant_err = get_variant_and_graphic_data(sample_id)
    if variant_err:
        result["errors"].append(variant_err)

    # Creating context variable to be serialized
    context = {
        "actions_qs": actions_qs,
        "gisaid_qs": gisaid_qs,
        "ena_qs": ena_qs,
        "bioinfo_qs": bioinfo_qs,
        "lineage_qs": lineage_qs,
    }


    # Serialize data and create results
    result["data"] = core.serializers.SampleDisplaySerializer(
        sample_obj,
        context=context,
        many=False
        ).data
    result["data"]["variant"] = variant_data
    result["data"]["graphic"] = graphic_data

    # Validate whether process succeed
    result["success"] = len(result["errors"]) == 0
    return result


def get_public_info(p_type, sample_id):
    return list(
        core.models.PublicDatabaseValues.objects
        .filter(
            sampleID__pk=sample_id,
            public_database_fieldID__database_type__public_type_name__iexact=p_type,
        )
        .values_list("public_database_fieldID__label_name", "value")
    )

