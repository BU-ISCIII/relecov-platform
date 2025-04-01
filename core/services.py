from django.db.models import Count
from django.contrib.auth.models import Group
import core.models
import core.serializers
import core.config
import core.utils.rest_api
from django.db.models import Q

def get_configuration_value(parameter_name):
    """Get a value from the configuration model."""
    return (
        core.models.ConfigSetting.objects
        .filter(configuration_name=parameter_name)
        .values_list("configuration_value", flat=True)
        .last()
    ) or "False"


def count_samples_by_state():
    """Count number of samples by state."""
    return (
        core.models.SampleStateHistory.objects
        .values("state_id__state")
        .annotate(count=Count("id"))
    )

def get_recent_samples(limit=10):
    samples = core.models.Sample.objects.order_by("-created_at")[:limit]
    return core.serializers.SampleSerializer(samples, many=True).data


def get_index_data():
    """Pack index data and return dict."""
    return {
        "number_of_samples": count_samples_by_state(),
        "recent_samples": get_recent_samples(),
        "nextstrain_url": get_configuration_value("NEXTSTRAIN_URL")
    }


def assign_samples_to_user_by_lab(lab, user_id):
    """Asign labortory samples to a new user."""
    if not user_id:
        return {"ERROR": "No user selected. Please choose a user before submitting."}

    try:
        user_obj = core.models.User.objects.get(pk=user_id)
    except core.models.User.DoesNotExist:
        return {"ERROR": f"User with ID {user_id} does not exist."}

    samples_qs = core.models.Sample.objects.filter(collecting_institution__iexact=lab)

    if samples_qs.exists():
        samples_qs.update(user=user_obj)
        return {"SUCCESS": "Samples successfully reassigned."}
    return {"ERROR": f"{core.config.ERROR_NO_SAMPLES_ARE_ASSIGNED_TO_LAB} {lab}"}


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


def display_samples(sample_name, lab_name, sample_state, s_date, user):
    """Sample filtering accoding to specific params and return serialized data."""

    sample_objs = core.models.Sample.objects.all()

    if lab_name:
        sample_objs = sample_objs.filter(collecting_institution__iexact=lab_name)

    if sample_name:
        exact_qs = sample_objs.filter(
            Q(sequencing_sample_id__iexact=sample_name)
            | Q(collecting_lab_sample_id__iexact=sample_name)
        )
        if exact_qs.count() == 1:
            return {"redirect": exact_qs.first().pk}
        elif exact_qs.exists():
            sample_objs = exact_qs
        else:
            partial_qs = sample_objs.filter(
                Q(sequencing_sample_id__icontains=sample_name)
                | Q(collecting_lab_sample_id__icontains=sample_name)
            )
            if partial_qs.count() == 1:
                return {"redirect": partial_qs.first().pk}
            elif not partial_qs.exists():
                return {"warning": core.config.ERROR_NOT_MATCHED_ITEMS_IN_SEARCH}
            sample_objs = partial_qs

    if sample_state:
        sample_ids = core.models.SampleStateHistory.objects.filter(
            state_id__pk=sample_state
        ).values_list("sample__pk", flat=True)
        sample_objs = sample_objs.filter(pk__in=sample_ids)

    if s_date:
        sample_objs = sample_objs.filter(created_at__exact=s_date)

    if not sample_objs.exists():
        return {"warning": core.config.ERROR_NOT_MATCHED_ITEMS_IN_SEARCH}

    if sample_objs.count() == 1:
        return {"redirect": sample_objs.first().pk}

    serialized_samples = core.serializers.SampleSearchResultSerializer(sample_objs, many=True).data

    return {
        "list_display": {
            "s_data": serialized_samples,
            "heading": core.config.HEADING_FOR_SAMPLE_LIST,
        }
    }

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
        "sample_gauge_graph": core.utils.samples.perc_gauge_graphic(analysis_percent),
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

    gisaid_raw = core.utils.public_db.get_public_accession_from_sample_lab("gisaid_accession_id")
    ena_raw = core.utils.public_db.get_public_accession_from_sample_lab("ena_sample_accession")
    actions_raw = core.utils.samples.get_lab_last_actions()

    data = {
        "sample_bar_graph": core.utils.samples.create_date_sample_bar(all_sample_per_date, bar_config),
        "sample_gauge_graph": core.utils.samples.perc_gauge_graphic(analysis_percent),
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
