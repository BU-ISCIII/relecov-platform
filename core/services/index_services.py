from django.db.models import Count

import core.models
import core.serializers


def get_configuration_value(parameter_name):
    """Get a value from the configuration model."""
    return (
        core.models.ConfigSetting.objects.filter(configuration_name=parameter_name)
        .values_list("configuration_value", flat=True)
        .last()
        or "False"
    )


def get_sample_count_qs():
    """Count number of samples by state."""
    return core.models.SampleStateHistory.objects.values("state_id__state").annotate(
        count=Count("id")
    )


def get_index_data():
    """Collect information required for the index view."""
    result = {"data": {}, "success": False, "errors": []}

    try:
        sample_count_qs = get_sample_count_qs()
        serialized = core.serializers.SampleCountByStateSerializer(
            sample_count_qs, many=True
        ).data
        result["data"]["number_of_samples"] = {
            entry["label"]: entry["count"] for entry in serialized
        }
    except Exception as exc:
        result["errors"].append(
            {"code": 500, "message": f"Error loading sample counts: {exc}"}
        )

    try:
        result["data"]["nextstrain_url"] = get_configuration_value("NEXTSTRAIN_URL")
    except Exception as exc:
        result["errors"].append(
            {"code": 500, "message": f"Error loading Nextstrain URL: {exc}"}
        )

    result["success"] = len(result["errors"]) == 0
    return result
