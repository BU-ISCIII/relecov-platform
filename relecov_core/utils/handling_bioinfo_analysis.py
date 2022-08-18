from relecov_core.models import BioinfoAnalysisField, BioInfoAnalysisValue


def get_bioinfo_analysis_data_from_sample(sample_obj):
    """Get the bioinfo analysis for the sample"""
    # Get the schema ID for filtering Fields
    schema_obj = sample_obj.get_schema_obj()
    a_data = []
    if not BioinfoAnalysisField.objects.filter(schema_id=schema_obj).exists():
        return None
    a_fields = BioinfoAnalysisField.objects.filter(schema_id=schema_obj)
    for a_field in a_fields:
        if BioInfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID=a_field, sampleID_id=sample_obj
        ).exists():
            value = (
                BioInfoAnalysisValue.objects.filter(
                    bioinfo_analysis_fieldID=a_field, sampleID_id=sample_obj
                )
                .last()
                .get_value()
            )
        else:
            value = ""
        a_data.append([a_field.get_label(), value])
    return a_data
