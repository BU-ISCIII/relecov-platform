from django.contrib.auth.models import Group
from django.db.models import Max, OuterRef, Subquery

from .search_services import get_search_data, validate_search_params, display_samples

import core.config
import core.models
import core.serializers
import core.utils.samples_map
import core.utils.samples_graphics
import core.utils.variants


# Sample display helpers

def get_sample_obj_from_id(sample_id):
    """Return the sample instance from its id."""
    if core.models.Sample.objects.filter(pk__exact=sample_id).exists():
        return core.models.Sample.objects.filter(pk__exact=sample_id).last()
    return None


def get_actions_qs(sample_obj):
    try:
        actions_qs = core.models.SampleStateHistory.objects.filter(
            sample=sample_obj
        ).order_by("-changed_at")
        return actions_qs, None
    except Exception as exc:
        return [], {"code": 500, "message": f"Error fetching actions: {exc}"}


def get_public_db_qs(sample_obj, db_name):
    try:
        qs = core.models.PublicDatabaseValues.objects.filter(
            sampleID=sample_obj,
            public_database_fieldID__database_type__public_type_name__iexact=db_name,
        )
        return qs, None
    except Exception as exc:
        return [], {
            "code": 500,
            "message": f"Error fetching public DB '{db_name}': {exc}",
        }


def get_bioinfo_qs(sample_obj):
    try:
        schema_obj = sample_obj.get_schema_obj()
        if not schema_obj:
            return [], {"code": 404, "message": "Schema not found for sample"}

        bioan_fields_qs = core.models.MetadataValues.objects.filter(
            schema_property__schemaID=schema_obj,
            sample=sample_obj,
        )
        latest_analysis_date = bioan_fields_qs.aggregate(Max("analysis_date"))["analysis_date__max"]
        if not latest_analysis_date:
            return [], {"code": 404, "message": "No bioinformatics analysis date found"}

        filtered_qs = bioan_fields_qs.filter(
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
        return filtered_qs, None
    except Exception as exc:
        return [], {"code": 500, "message": f"Error fetching bioinfo data: {exc}"}


def get_lineage_qs(sample_obj):
    try:
        schema_obj = sample_obj.get_schema_obj()
        if not schema_obj:
            return [], {"code": 404, "message": "Schema not found for sample"}

        lineage_fields = core.models.LineageFields.objects.filter(schemaID=schema_obj)
        lineage_qs = []
        for field in lineage_fields:
            value_qs = core.models.LineageValues.objects.filter(
                lineage_fieldID=field, sample=sample_obj
            ).order_by("-generated_at")
            if value_qs.exists():
                lineage_qs.append(value_qs.first())

        return lineage_qs, None
    except Exception as exc:
        return [], {"code": 500, "message": f"Error fetching lineage data: {exc}"}


def get_variant_and_graphic_data(sample_id):
    variant_data = {}
    graphic_data = None
    try:
        variant_data = core.utils.variants.get_variant_qs(sample_id)
        if "heading" in variant_data:
            graphic_data = core.utils.variants.get_variant_graphic_from_sample(sample_id)
    except Exception as exc:
        return None, None, {"code": 500, "message": f"Error getting variant data: {exc}"}
    return variant_data, graphic_data, None


def get_sample_display_data(sample_id, user):
    """Collect all information required to display a sample."""
    result = {"data": {}, "success": False, "errors": []}

    sample_obj = get_sample_obj_from_id(sample_id)
    if not sample_obj:
        result["errors"].append({"code": 404, "message": core.config.ERROR_SAMPLE_DOES_NOT_EXIST})
        return result

    group = Group.objects.get(name="RelecovManager")
    if group not in user.groups.all():
        lab_name = sample_obj.get_collecting_institution()
        if not core.models.Profile.objects.filter(user=user, laboratory__iexact=lab_name).exists():
            result["errors"].append({"code": 403, "message": core.config.ERROR_NOT_ALLOWED_TO_SEE_THE_SAMPLE})
            return result

    actions_qs, err = get_actions_qs(sample_obj)
    if err:
        result["errors"].append(err)

    gisaid_qs, err = get_public_db_qs(sample_obj, "gisaid")
    if err:
        result["errors"].append(err)

    ena_qs, err = get_public_db_qs(sample_obj, "ena")
    if err:
        result["errors"].append(err)

    bioinfo_qs, err = get_bioinfo_qs(sample_obj)
    if err:
        result["errors"].append(err)

    lineage_qs, err = get_lineage_qs(sample_obj)
    if err:
        result["errors"].append(err)

    variant_data, graphic_data, variant_err = get_variant_and_graphic_data(sample_id)
    if variant_err:
        result["errors"].append(variant_err)

    context = {
        "actions_qs": actions_qs,
        "gisaid_qs": gisaid_qs,
        "ena_qs": ena_qs,
        "bioinfo_qs": bioinfo_qs,
        "lineage_qs": lineage_qs,
    }

    result["data"] = core.serializers.SampleDisplaySerializer(sample_obj, context=context, many=False).data
    result["data"]["variant"] = variant_data
    result["data"]["graphic"] = graphic_data
    result["success"] = len(result["errors"]) == 0
    return result


# Existing service functions

def handle_sample_search(action=None, sample_name="", s_date="", lab_name="", sample_state="", user=None):
    """Orchestrate sample search workflow."""
    result = {"data": {}, "success": False, "errors": []}

    result["data"].update(get_search_data(user_obj=user))

    if action != "searchSample":
        return result

    validation = validate_search_params(sample_name, lab_name, sample_state, s_date)
    if "warning" in validation:
        result["errors"].append({"code": 400, "message": validation["warning"]})
        return result

    display_result = display_samples(
        sample_name=sample_name,
        lab_name=lab_name,
        sample_state=sample_state,
        s_date=s_date,
        user=user,
    )
    result["data"].update(display_result.get("data", {}))
    result["errors"].extend(display_result.get("errors", []))
    result["success"] = display_result.get("success", False) and not result["errors"]
    return result


def get_received_samples_data():
    """Gather dashboard information about received samples."""
    result = {"data": {}, "success": False, "errors": []}
    sample_data = {}

    try:
        map_result = core.utils.samples_map.create_samples_received_map()
        sample_data["map"] = map_result
        if isinstance(map_result, dict) and map_result.get("ERROR"):
            result["errors"].append({"code": 500, "message": map_result["ERROR"]})
    except Exception as exc:
        result["errors"].append({"code": 500, "message": f"Error generating map: {exc}"})
        sample_data["map"] = {}

    try:
        sample_data["received_samples_graph"] = core.utils.samples_graphics.received_samples_graph()
    except Exception as exc:
        result["errors"].append({"code": 500, "message": f"Error generating samples graph: {exc}"})
        sample_data["received_samples_graph"] = {}

    try:
        per_ccaa = core.utils.samples_graphics.received_per_ccaa()
        sample_data["samples_per_ccaa"] = per_ccaa
        if isinstance(per_ccaa, dict) and per_ccaa.get("ERROR"):
            result["errors"].append({"code": 500, "message": per_ccaa["ERROR"]})
    except Exception as exc:
        result["errors"].append({"code": 500, "message": f"Error generating CCAA chart: {exc}"})
        sample_data["samples_per_ccaa"] = {}

    try:
        per_lab = core.utils.samples_graphics.received_per_lab()
        sample_data["samples_per_lab"] = per_lab
        if isinstance(per_lab, dict) and per_lab.get("ERROR"):
            result["errors"].append({"code": 500, "message": per_lab["ERROR"]})
    except Exception as exc:
        result["errors"].append({"code": 500, "message": f"Error generating laboratory chart: {exc}"})
        sample_data["samples_per_lab"] = {}

    result["data"]["sample_data"] = sample_data
    result["success"] = len(result["errors"]) == 0
    return result
