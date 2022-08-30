from relecov_core.models import Schema


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
