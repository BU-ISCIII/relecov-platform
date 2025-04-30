# Local imports
import core.utils.samples
import core.models


def get_lineages_list():
    """Function gets the lab names and return then in an ordered list"""
    return list(
        core.models.LineageValues.objects.all()
        .values_list("value", flat=True)
        .distinct()
        .order_by("value")
    )

# TODO: I think this is in services.py. And not needed anymore here. 
def get_lineage_data_from_sample(sample_id):
    """Get the bioinfo analysis for the sample"""
    sample_obj = core.utils.samples.get_sample_obj_from_id(sample_id)
    if not sample_obj:
        return None
    # Get the schema ID for filtering Fields
    schema_obj = sample_obj.get_schema_obj()
    a_data = []
    if not core.models.LineageFields.objects.filter(schemaID=schema_obj).exists():
        return None
    a_fields = core.models.LineageFields.objects.filter(schemaID=schema_obj)
    for a_field in a_fields:
        sample_lineage_fields = core.models.LineageValues.objects.filter(
            lineage_fieldID=a_field, sample=sample_obj
        )
        if sample_lineage_fields.exists():
            value = sample_lineage_fields.last().get_value()
        else:
            value = ""
        a_data.append([a_field.get_lineage_property_name(), value])
    return a_data
