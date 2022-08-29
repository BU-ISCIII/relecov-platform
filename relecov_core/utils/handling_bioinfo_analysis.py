from relecov_core.models import BioinfoAnalysisField, BioInfoAnalysisValue, Schema

from relecov_core.utils.handling_samples import get_sample_obj_from_id, get_samples_count_per_schema

from relecov_core.utils.schema_handling import get_schema_obj_from_id


def get_bioinfo_analysis_data_from_sample(sample_id):
    """Get the bioinfo analysis for the sample"""
    sample_obj = get_sample_obj_from_id(sample_id)
    if not sample_obj:
        return None
    # Get the schema ID for filtering Fields
    schema_obj = sample_obj.get_schema_obj()
    a_data = []
    if not BioinfoAnalysisField.objects.filter(schemaID=schema_obj).exists():
        return None
    a_fields = BioinfoAnalysisField.objects.filter(schemaID=schema_obj)
    for a_field in a_fields:
        if BioInfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID=a_field, sample=sample_obj
        ).exists():
            value = (
                BioInfoAnalysisValue.objects.filter(
                    bioinfo_analysis_fieldID=a_field, sample=sample_obj
                )
                .last()
                .get_value()
            )
        else:
            value = ""
        a_data.append([a_field.get_label(), value])
    return a_data


def get_bioinfo_analyis_fields_utilization(schema_id=None):
    """Get the level of utilization for the bioinfo analysis fields.
    If schema is not given, the function retrun a separate info for all
    schemas
    """
    b_data = {}
    if schema_id is None:
        if Schema.objects.all().exists():
            schema_objs = Schema.objects.all()
        else:
            return None
    else:
        schema_obj = get_schema_obj_from_id(schema_id)
        if schema_obj is None:
            return None
        schema_objs = [schema_obj]
    for schema_obj in schema_objs:
        # get field names
        if not BioinfoAnalysisField.objects.filter(schemaID=schema_obj).exists():
            continue

        schema_name = schema_obj.get_schema_name()
        num_samples_in_sch = get_samples_count_per_schema(schema_name)
        b_data[schema_name] = {}
        b_field_objs = BioinfoAnalysisField.objects.filter(schemaID=schema_obj)
        for b_field_obj in b_field_objs:
            f_name = b_field_obj.get_label()
            if not BioInfoAnalysisValue.objects.filter(
                bioinfo_analysis_fieldID=b_field_obj
            ).exists():
                b_data[schema_name][f_name] = "never_used"
                continue
            # b_data[schema_name][f_name] = [count]
            count_not_empty = BioInfoAnalysisValue.objects.filter(
                bioinfo_analysis_fieldID=b_field_obj
            ).exclude(value="None").count()
            try:
                b_data[schema_name][f_name] = count_not_empty/num_samples_in_sch
            except ZeroDivisionError:
                b_data[schema_name][f_name] = 0
    return b_data
