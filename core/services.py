from django.db.models import Count
import core.models
import core.serializers
import core.config
import core.utils.rest_api


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
