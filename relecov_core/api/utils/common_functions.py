from relecov_core.models import Schema

from relecov_core.api.serializers import CreateDateAfterChangeStateSerializer


def get_schema_version_if_exists(data):
    """Check if schema name and schema version exists"""
    apps_name = __package__.split(".")[0]

    if "schema_name" in data and "schema_version" in data:
        if Schema.objects.filter(
            schema_name__iexact=data["schema_name"],
            schema_version__iexact=data["schema_version"],
            schema_apps_name__iexact=apps_name,
        ).exists():
            return Schema.objects.filter(
                schema_name__iexact=data["schema_name"],
                schema_version__iexact=data["schema_version"],
                schema_apps_name__iexact=apps_name,
            ).last()
    return None


def update_change_state_date(sample_id, state_id):
    """Update the DateUpdateState table with the new sample state"""
    d_date = {"stateID": state_id, "sampleID": sample_id}
    date_update_serializer = CreateDateAfterChangeStateSerializer(d_date)
    if date_update_serializer.isvalid():
        date_update_serializer.save()
