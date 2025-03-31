from django.db.models import Count
import core.models
import core.serializers

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
