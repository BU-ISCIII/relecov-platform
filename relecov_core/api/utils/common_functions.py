from relecov_core.models import Schema, AnalysisType


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


def get_analysis_type_id(type):
    if AnalysisType.objects.filter(type_name__iexact=type).exists():
        return AnalysisType.objects.filter(type_name__iexact=type).last().get_id()
    return None
