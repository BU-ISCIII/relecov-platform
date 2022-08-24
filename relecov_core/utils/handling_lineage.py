from relecov_core.utils.handling_samples import get_sample_obj_from_id
from relecov_core.models import LineageFields, LineageValues


def get_lineage_data_from_sample(sample_id):
    """Get the bioinfo analysis for the sample"""
    sample_obj = get_sample_obj_from_id(sample_id)
    if not sample_obj:
        return None
    # Get the schema ID for filtering Fields
    schema_obj = sample_obj.get_schema_obj()
    a_data = []
    if not LineageFields.objects.filter(schemaID=schema_obj).exists():
        return None
    a_fields = LineageFields.objects.filter(schemaID=schema_obj)
    for a_field in a_fields:
        if LineageValues.objects.filter(
            lineage_fieldID=a_field, sample=sample_obj
        ).exists():
            value = (
                LineageValues.objects.filter(
                    lineage_fieldID=a_field, sample=sample_obj
                )
                .last()
                .get_value()
            )
        else:
            value = ""
        a_data.append([a_field.get_lineage_property_name(), value])
    return a_data
