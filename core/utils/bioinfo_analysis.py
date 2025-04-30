# Local imports
import core.models
import core.utils.samples
import core.utils.schema
from django.db.models import Max, Subquery, OuterRef


def get_bio_analysis_stats_from_lab(lab_name=None):
    """Get the number of samples that are analized and compare with the number
    of recieved samples. If no lab name is given it matches all labs
    """
    bio_stats = {}
    if lab_name is None:
        bioqry = core.models.SampleStateHistory.objects.filter(
            state__state__iexact="Bioinfo"
        )
        bio_stats["analized"] = bioqry.values("sample_id").distinct().count()
        bio_stats["received"] = core.models.Sample.objects.all().count()
    else:
        sample_objs = core.models.Sample.objects.filter(
            collecting_institution__iexact=lab_name
        )
        bioqry = core.models.SampleStateHistory.objects.filter(
            state__state__iexact="Bioinfo"
        )
        samples_bioquery = bioqry.filter(sample__in=sample_objs)
        bio_stats["analized"] = samples_bioquery.values("sample_id").distinct().count()
        bio_stats["received"] = len(sample_objs)
    return bio_stats


def get_bioinfo_analysis_data_from_sample(sample_id):
    """Get the latest bioinfo analysis data for the sample, ensuring unique values"""

    # Retrieve the sample object
    sample_obj = core.utils.samples.get_sample_obj_from_id(sample_id)
    if not sample_obj:
        return None

    # Get the schema ID for filtering Fields
    schema_obj = sample_obj.get_schema_obj()
    bio_anlys_data = []

    # Ensure schema_obj is valid
    if not schema_obj:
        return None

    # Get all MetadataValues related to the schema and sample
    bioan_fields_qs = core.models.MetadataValues.objects.filter(
        schema_property__schemaID=schema_obj,
        sample=sample_obj,  # Ensure we only fetch for this specific sample
    )

    # Get the latest analysis_date for this sample
    latest_analysis_date = bioan_fields_qs.aggregate(Max("analysis_date"))[
        "analysis_date__max"
    ]

    # If no data exists, return None
    if not latest_analysis_date:
        return []

    # Find the latest generated_at for each unique value and schema_property_id
    latest_bioan_fields = bioan_fields_qs.filter(
        analysis_date=latest_analysis_date,
        generated_at=Subquery(
            bioan_fields_qs.filter(
                analysis_date=latest_analysis_date,
                schema_property=OuterRef("schema_property"),
                value=OuterRef("value"),
            )
            .order_by("-generated_at")
            .values("generated_at")[:1]
        ),
    )

    # If still empty, return None
    if not latest_bioan_fields.exists():
        return None

    # Iterate through the unique latest bioan_fields queryset
    for bio_field in latest_bioan_fields:
        value = bio_field.get_value() if bio_field else ""

        bio_anlys_data.append([bio_field.schema_property.get_label(), value])
    return bio_anlys_data


# FIXME: This is not invoked in the project
def get_bioinfo_analyis_fields_utilization(schema_obj=None):
    """Get the level of utilization for the bioinfo analysis fields.
    If schema is not given, the function get the latest default schema
    """
    b_data = {}
    if schema_obj is None:
        schema_obj = core.utils.schema.get_default_schema()

    # get field names
    b_field_objs = core.models.SchemaProperties.objects.filter(
        schemaID=schema_obj,
        classificationID__classification_name__icontains="Bioinformatic",
    )

    if not b_field_objs.exists():
        return b_data

    num_samples_in_sch = core.utils.samples.get_samples_count_per_schema(
        schema_obj.get_schema_name()
    )
    if num_samples_in_sch == 0:
        return b_data
    b_data = {
        "never_used": [],
        "always_none": [],
        "fields_norm": {},
        "fields_value": {},
    }
    for b_field_obj in b_field_objs:
        f_name = b_field_obj.get_label()
        b_field_obj_info = (
            core.models.MetadataValues.objects.filter(schema_property__in=b_field_objs)
            .values("schema_property")
            .annotate(latest_generated_at=Max("generated_at"))
        )
        if not b_field_obj_info.exists():
            b_data["never_used"].append(f_name)
            b_data["fields_value"][f_name] = 0
            continue
        # b_data[schema_name][f_name] = [count]
        count_not_empty = b_field_obj_info.exclude(value__in=["None", ""]).count()
        b_data["fields_value"][f_name] = count_not_empty
        if count_not_empty == 0:
            b_data["always_none"].append(f_name)
            continue

        try:
            b_data["fields_norm"][f_name] = count_not_empty / num_samples_in_sch
        except ZeroDivisionError:
            b_data["fields_norm"][f_name] = 0
    b_data["num_fields"] = len(b_field_objs)

    return b_data
