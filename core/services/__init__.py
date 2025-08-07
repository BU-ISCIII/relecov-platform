from django.db.models import Count, Q, Max, OuterRef, Subquery
from django.contrib.auth.models import Group
from django.db.models.functions import TruncDate
from collections import OrderedDict

import core.models
import core.serializers
import core.config
import core.utils.utils
import core.utils.rest_api
import core.utils.schema
import core.utils.variants
import core.utils.samples
import core.utils.labs
import core.utils.bioinfo_analysis
import core.utils.generic_functions
import json

# TODO: Some functions are still being called from utils.py.
# Move those functions into proper service modules and import them accordingly.
# Keep utils.py only for generic utilities (e.g., data processing, conversions, etc.).
# TODO: add docsrings and sort functions.
# TODO: There are several functions in utils* that have been reimplemented here. Clean them to avoid duplicates


# util
def get_configuration_value(parameter_name):
    """Get a value from the configuration model."""
    return (
        core.models.ConfigSetting.objects.filter(configuration_name=parameter_name)
        .values_list("configuration_value", flat=True)
        .last()
    ) or "False"


# util
def get_sample_count_qs():
    """Count number of samples by state."""
    return core.models.SampleStateHistory.objects.values("state_id__state").annotate(
        count=Count("id")
    )


# service
def get_index_data():
    result = {"data": {}, "success": False, "errors": []}

    # Get sample counts by state and serialize data
    try:
        sample_count_qs = get_sample_count_qs()
        serialized = core.serializers.SampleCountByStateSerializer(
            sample_count_qs, many=True
        ).data
        # Transform data structur
        result["data"]["number_of_samples"] = {
            entry["label"]: entry["count"] for entry in serialized
        }
    except Exception as e:
        result["errors"].append(
            {"code": 500, "message": f"Error loading sample counts: {str(e)}"}
        )

    # Get Nextrain configuration
    try:
        result["data"]["nextstrain_url"] = get_configuration_value("NEXTSTRAIN_URL")
    except Exception as e:
        result["errors"].append(
            {"code": 500, "message": f"Error loading Nextstrain URL: {str(e)}"}
        )

    # Return success
    result["success"] = len(result["errors"]) == 0
    return result


def get_sample_obj_from_id(sample_id):
    """Return the sample instance from its id"""
    if core.models.Sample.objects.filter(pk__exact=sample_id).exists():
        return core.models.Sample.objects.filter(pk__exact=sample_id).last()
    return None


# FIXME: refactor its output
def get_search_data(user_obj):
    """Structure data to render form in search sample view."""
    if core.models.Sample.objects.count() == 0:
        return {"ERROR": core.config.ERROR_NOT_SAMPLES_HAVE_BEEN_DEFINED}

    # Serialize available states request
    states_qs = core.models.SampleState.objects.all()
    serialized_states = core.serializers.SampleStateSerializer(
        states_qs, many=True
    ).data

    # Get laboratories available in the user's group
    group = Group.objects.get(name="RelecovManager")
    if group in user_obj.groups.all():
        labs = core.utils.labs.get_all_defined_labs()
        if isinstance(labs, dict) and "ERROR" in labs:
            labs = ["", ""]
    else:
        labs = [core.utils.labs.get_lab_name_from_user(user_obj)]

    return {
        "labs": labs,
        "states": serialized_states,
    }


def validate_search_params(sample_name, lab_name, sample_state, s_date):
    """Validates search parameters and returns warnings if applicable."""
    if not any([sample_name, lab_name, sample_state, s_date]):
        return {"warning": "You must fill in at least one field to search."}
    if s_date and not core.utils.generic_functions.check_valid_date_format(s_date):
        return {"warning": core.config.ERROR_INVALID_DEFINED_SAMPLE_FORMAT}
    return {}


def display_samples(sample_name, lab_name, sample_state, s_date, user):
    """"""
    result = {"data": {}, "success": False, "errors": []}

    samples_qs = core.models.Sample.objects.all()

    if lab_name:
        samples_qs = samples_qs.filter(collecting_institution__iexact=lab_name)

    if sample_name:
        exact_qs = samples_qs.filter(
            Q(sequencing_sample_id__iexact=sample_name)
            | Q(collecting_lab_sample_id__iexact=sample_name)
        )
        if exact_qs.exists():
            samples_qs = exact_qs
        else:
            partial_qs = samples_qs.filter(
                Q(sequencing_sample_id__icontains=sample_name)
                | Q(collecting_lab_sample_id__icontains=sample_name)
            )
            if partial_qs.exists():
                samples_qs = partial_qs
            else:
                result["data"] = {
                    "samples": [],
                    "heading": core.config.HEADING_FOR_SAMPLE_LIST,
                    "redirect": None,
                }
                result["errors"].append(core.config.ERROR_NOT_MATCHED_ITEMS_IN_SEARCH)
                return result

    if sample_state:
        sample_ids = core.models.SampleStateHistory.objects.filter(
            state_id__pk=sample_state
        ).values_list("sample__pk", flat=True)
        samples_qs = samples_qs.filter(pk__in=sample_ids)

    if s_date:
        samples_qs = samples_qs.filter(created_at__exact=s_date)

    if not samples_qs.exists():
        result["data"] = {
            "samples": [],
            "heading": core.config.HEADING_FOR_SAMPLE_LIST,
            "redirect": None,
        }
        result["errors"].append(core.config.ERROR_NOT_MATCHED_ITEMS_IN_SEARCH)
        return result

    if samples_qs.count() == 1:
        result["data"] = {
            "samples": [],
            "heading": core.config.HEADING_FOR_SAMPLE_LIST,
            "redirect": samples_qs.first().pk,
        }
        result["success"] = True
        return result

    serialized = core.serializers.SampleSearchResultSerializer(
        samples_qs, many=True
    ).data

    result["data"] = {
        "samples": serialized,
        "heading": core.config.HEADING_FOR_SAMPLE_LIST,
        "redirect": None,
    }
    result["success"] = True
    return result


# FIXME: refactor its output
def get_sample_per_date_per_all_lab(detailed=False):
    """
    Return number of samples per sequencing date (grouped by date).

    - If `detailed` is False (default), return global counts (date -> count).
    - If `detailed` is True, return per-lab counts: [{"lab_name": ..., "date": ..., "num_samples": ...}, ...]
    """
    if not detailed:
        samples_by_date = (
            core.models.Sample.objects.annotate(date_only=TruncDate("sequencing_date"))
            .values("date_only")
            .annotate(count=Count("id"))
            .order_by("date_only")
        )

        result = OrderedDict()
        for entry in samples_by_date:
            formatted_date = entry["date_only"].strftime("%d-%B-%Y")
            result[formatted_date] = entry["count"]
        return result

    else:
        samples_by_lab_and_date = (
            core.models.Sample.objects.exclude(sequencing_date__isnull=True)
            .annotate(date_only=TruncDate("sequencing_date"))
            .values("collecting_institution", "date_only")
            .annotate(count=Count("id"))
            .order_by("collecting_institution", "date_only")
        )

        result = []
        for entry in samples_by_lab_and_date:
            result.append(
                {
                    "lab_name": entry["collecting_institution"],
                    "date": entry["date_only"].strftime("%d-%B-%Y"),
                    "num_samples": entry["count"],
                }
            )
        return result


def get_intranet_data_for_manager():
    result = {"data": {}, "success": False, "errors": []}
    try:
        all_sample_per_date = core.utils.samples.get_sample_per_date_per_all_lab()
        num_of_samples = core.utils.samples.count_handled_samples()
        analysis_percent = core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab()

        bar_config = {
            "col_names": ["Sequencing Date", "Number of samples"],
            "options": {
                "title": "Samples Received for all laboratories",
                "width": 590,
            },
        }

        # dash graph for samples per lab
        core.utils.samples.create_dash_bar_for_each_lab()

        # Collect data that populate views
        gisaid_raw = core.utils.public_db.get_public_accession_from_sample_lab(
            "gisaid_accession_id"
        )
        ena_raw = core.utils.public_db.get_public_accession_from_sample_lab(
            "ena_sample_accession"
        )
        actions_raw = core.utils.samples.get_lab_last_actions()
        data = {
            "sample_bar_graph": core.utils.samples.create_date_sample_bar(
                all_sample_per_date, bar_config
            ),
            "sample_gauge_graph": core.utils.utils.perc_gauge_graphic(analysis_percent),
            "actions": core.serializers.LabLastActionSerializer.from_raw(actions_raw),
        }

        if gisaid_raw:
            data["gisaid_accession"] = core.serializers.PublicAccessionSerializer.from_raw(
                gisaid_raw
            )
            data["gisaid_graph"] = core.utils.public_db.percentage_graphic(
                num_of_samples.get("Defined", 0), len(gisaid_raw), ""
            )

        if ena_raw:
            data["ena_accession"] = core.serializers.PublicAccessionSerializer.from_raw(
                ena_raw
            )
            data["ena_graph"] = core.utils.public_db.percentage_graphic(
                num_of_samples.get("Defined", 0), len(ena_raw), ""
            )

        result["data"] = data
        result["success"] = True
    except Exception as e:
        result["errors"].append(str(e))
        result["success"] = False
    return result


# FIXME: refactor its output


def get_intranet_data_for_user(user):
    lab_name = get_lab_name_from_user(user)
    date_lab_samples = core.utils.samples.get_sample_per_date_per_lab(lab_name)

    if not date_lab_samples:
        return f"No samples found for selected laboratory: {lab_name}"

    sample_lab_objs = core.utils.samples.get_sample_objs_per_lab(lab_name)
    analysis_percent = core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab(
        lab_name
    )

    bar_config = {
        "col_names": ["Sequencing Date", "Number of samples"],
        "options": {
            "title": "Samples Received",
            "width": 600,
        },
    }

    gisaid_raw = core.utils.public_db.get_public_accession_from_sample_lab(
        "gisaid_accession_id", sample_lab_objs
    )
    ena_raw = core.utils.public_db.get_public_accession_from_sample_lab(
        "ena_sample_accession", sample_lab_objs
    )
    actions_raw = core.utils.samples.get_lab_last_actions(lab_name)

    intra_data = {
        "sample_bar_graph": core.utils.samples.create_date_sample_bar(
            date_lab_samples, bar_config
        ),
        "sample_gauge_graph": core.utils.utils.perc_gauge_graphic(analysis_percent),
        "actions": core.serializers.LabLastActionDictSerializer.from_raw(actions_raw),
    }

    if gisaid_raw:
        intra_data["gisaid_accession"] = (
            core.serializers.PublicAccessionSerializer.from_raw(gisaid_raw)
        )
        intra_data["gisaid_graph"] = core.utils.public_db.percentage_graphic(
            len(sample_lab_objs), len(gisaid_raw), ""
        )

    if ena_raw:
        intra_data["ena_accession"] = (
            core.serializers.PublicAccessionSerializer.from_raw(ena_raw)
        )
        intra_data["ena_graph"] = core.utils.public_db.percentage_graphic(
            len(sample_lab_objs), len(ena_raw), ""
        )

    return intra_data


def get_actions_qs(sample_obj):
    try:
        actions_qs = core.models.SampleStateHistory.objects.filter(
            sample=sample_obj
        ).order_by("-changed_at")
        return actions_qs, None
    except Exception as e:
        return [], {"code": 500, "message": f"Error fetching actions: {str(e)}"}


def get_public_db_qs(sample_obj, db_name):
    try:
        qs = core.models.PublicDatabaseValues.objects.filter(
            sampleID=sample_obj,
            public_database_fieldID__database_type__public_type_name__iexact=db_name,
        )
        return qs, None
    except Exception as e:
        return [], {
            "code": 500,
            "message": f"Error fetching public DB '{db_name}': {str(e)}",
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
        latest_analysis_date = bioan_fields_qs.aggregate(Max("analysis_date"))[
            "analysis_date__max"
        ]
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
    except Exception as e:
        return [], {"code": 500, "message": f"Error fetching bioinfo data: {str(e)}"}


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
    except Exception as e:
        return [], {"code": 500, "message": f"Error fetching lineage data: {str(e)}"}


def get_variant_and_graphic_data(sample_id):
    variant_data = {}
    graphic_data = None
    try:
        # Load variant data
        variant_data = core.utils.variants.get_variant_qs(sample_id)
        if "heading" in variant_data:
            graphic_data = core.utils.variants.get_variant_graphic_from_sample(
                sample_id
            )
    except Exception as e:
        return (
            None,
            None,
            {"code": 500, "message": f"Error getting variant data: {str(e)}"},
        )
    return variant_data, graphic_data, None


def get_sample_display_data(sample_id, user):
    result = {"data": {}, "success": False, "errors": []}

    # Validate sample
    sample_obj = get_sample_obj_from_id(sample_id)
    if not sample_obj:
        result["errors"].append(
            {"code": 404, "message": core.config.ERROR_SAMPLE_DOES_NOT_EXIST}
        )
        return result

    # Check by group permissions
    group = Group.objects.get(name="RelecovManager")
    if group not in user.groups.all():
        lab_name = sample_obj.get_collecting_institution()
        if not core.models.Profile.objects.filter(
            user=user, laboratory__iexact=lab_name
        ).exists():
            result["errors"].append(
                {
                    "code": 403,
                    "message": core.config.ERROR_NOT_ALLOWED_TO_SEE_THE_SAMPLE,
                }
            )
            return result

    # Recover error handling
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

    # Generate variant data
    variant_data, graphic_data, variant_err = get_variant_and_graphic_data(sample_id)
    if variant_err:
        result["errors"].append(variant_err)

    # Creating context variable to be serialized
    context = {
        "actions_qs": actions_qs,
        "gisaid_qs": gisaid_qs,
        "ena_qs": ena_qs,
        "bioinfo_qs": bioinfo_qs,
        "lineage_qs": lineage_qs,
    }

    # Serialize data and create results
    result["data"] = core.serializers.SampleDisplaySerializer(
        sample_obj, context=context, many=False
    ).data
    result["data"]["variant"] = variant_data
    result["data"]["graphic"] = graphic_data

    # Validate whether process succeed
    result["success"] = len(result["errors"]) == 0
    return result


def get_public_info(p_type, sample_id):
    return list(
        core.models.PublicDatabaseValues.objects.filter(
            sampleID__pk=sample_id,
            public_database_fieldID__database_type__public_type_name__iexact=p_type,
        ).values_list("public_database_fieldID__label_name", "value")
    )


def get_schema_handling_data(request):
    """ """
    result = {"data": {}, "success": True, "errors": []}
    try:
        if request.method == "POST" and request.POST.get("action") == "uploadSchema":
            schema_default = "on" if "schemaDefault" in request.POST else "off"
            schema_data = core.utils.schema.process_schema_file(
                request.FILES.get("schemaFile"),
                schema_default,
                request.user,
                __package__,
            )
            if "ERROR" in schema_data:
                result["success"] = False
                result["errors"].append(schema_data["ERROR"])
            else:
                result["data"]["SUCCESS"] = schema_data.get("SUCCESS")
        #
        result["data"]["schemas"] = core.utils.schema.get_schemas_loaded(__package__)
    except Exception as e:
        result["success"] = False
        result["errors"].append(str(e))
    return result


def get_metadata_visualization_data(schema):
    data = {}
    for fill_mode in ["sample", "batch"]:
        qs = core.models.MetadataVisualization.objects.filter(
            schemaID=schema, fill_mode=fill_mode, in_use=True
        ).order_by("order")
        data[fill_mode] = core.serializers.MetadataVisualizationSerializer(
            qs, many=True
        ).data
    return data


def store_metadata_visualization_fields(schema_id, fields, fill_mode="sample"):
    """
    Store the selected fields for metadata visualization.
    'fields' should be a list of dicts: [{"property_name": ..., "label_name": ..., "order": ...}, ...]
    """
    # Remove previous visualization for this schema/fill_mode
    core.models.MetadataVisualization.objects.filter(
        schemaID=schema_id, fill_mode=fill_mode
    ).delete()
    # Create new visualization
    for field in fields:
        core.models.MetadataVisualization.objects.create(
            schemaID_id=schema_id,
            property_name=field["property_name"],
            label_name=field["label_name"],
            order=field["order"],
            in_use=True,
            fill_mode=fill_mode,
        )
    return True


def get_schema_fields_data(schema, template_labels=None):
    """Returns the serialized schema fields, and if there are template_labels, add ‘used’ and ‘order’."""
    qs = core.models.SchemaProperties.objects.filter(schemaID=schema).order_by("label")
    serialized = core.serializers.SchemaPropertiesSerializer(qs, many=True).data
    if template_labels:
        for field in serialized:
            label = field["label"].strip()
            if label in template_labels:
                field["used"] = True
                field["order"] = template_labels.index(label)
            else:
                field["used"] = False
                field["order"] = ""
    return serialized


def get_schema_fields_for_jexcel(schema, template_labels=None):
    """ "Returns the list of lists structure for JExcel, using the serialized data"""
    fields = get_schema_fields_data(schema, template_labels)
    return {
        "schema_id": str(schema.pk),
        "fields": [
            [
                f["property"],
                f["label"],
                f["order"],
                str(f["used"]).lower(),
                f["fill_mode"],
            ]
            for f in fields
        ],
    }


def handle_metadata_visualization(action=None, table_data_json=None):
    result = {"data": None, "success": None, "errors": []}
    # Get the latest schema in use
    try:
        schema = (
            core.models.Schema.objects.filter(schema_in_use=True)
            .order_by("-generated_at")
            .first()
        )
        if not schema:
            result["success"] = False
            result["errors"].append(core.config.ERROR_SCHEMA_NOT_DEFINED)
            return result

        if action == "selectFields":
            if not table_data_json:
                result["success"] = False
                result["errors"].append("No table_data provided in POST.")
                return result
            try:
                rows = json.loads(table_data_json)
            except Exception as e:
                result["success"] = False
                result["errors"].append(f"Error parsing table_data: {str(e)}")
                return result

            core.models.MetadataVisualization.objects.filter(schemaID=schema).delete()
            for row in rows:
                core.models.MetadataVisualization.objects.create(
                    schemaID=schema,
                    property_name=row[0],
                    label_name=row[1],
                    order=(row[2] if row[2] != "" else 0),  # Not sure what to use here
                    in_use=row[3],
                    fill_mode=row[4] if len(row) > 4 else "sample",
                )
            result["data"] = {"visualization": get_metadata_visualization_data(schema)}
            result["success"] = True
            return result

        if action == "deleteFields":
            core.models.MetadataVisualization.objects.filter(schemaID=schema).delete()
            result["data"] = {"deleted": True}
            result["success"] = True
            return result

        # GET o fallback: get data for visualization
        visualization = get_metadata_visualization_data(schema)
        if visualization["sample"] or visualization["batch"]:
            result["data"] = {"visualization": visualization}
        else:
            template_labels = core.utils.schema.get_fields_if_template()
            result["data"] = {
                "schema_fields": get_schema_fields_for_jexcel(schema, template_labels)
            }
        result["success"] = True
    except Exception as e:
        result["success"] = False
        result["errors"].append(str(e))
    return result


def handle_metadata_upload(metadata_file, username):
    result = {"data": {}, "success": False, "errors": []}
    try:
        core.utils.samples.save_excel_form_in_samba_folder(metadata_file, username)
        result["data"] = {"sample_recorded": {"ok": "OK"}}
        result["success"] = True
    except Exception as e:
        result["errors"].append(str(e))
    return result


def handle_define_samples(post_data, user, schema_obj):
    result = {"data": {}, "success": False, "errors": []}
    try:
        res_analyze = core.utils.samples.analyze_input_samples(post_data, user)
        if len(res_analyze) == 0:
            m_form = core.utils.samples.create_metadata_form(schema_obj, user)
            result["data"] = {"m_form": m_form}
            result["success"] = True
            return result
        if "save_samples" in res_analyze:
            s_saved = core.utils.samples.save_temp_sample_data(res_analyze["save_samples"], user)
            result["data"]["sample_saved"] = s_saved
        if "s_incomplete" in res_analyze or "s_already_record" in res_analyze:
            m_form = None
            if "s_incomplete" in res_analyze:
                m_form = core.utils.samples.create_metadata_form(schema_obj, user)
            result["data"] = {"sample_issues": res_analyze, "m_form": m_form}
            result["success"] = True
            return result
        m_batch_form = core.utils.samples.create_form_for_batch(schema_obj, user)
        sample_saved = core.utils.samples.get_sample_pre_recorded(user)
        result["data"] = {"m_batch_form": m_batch_form, "sample_saved": sample_saved}
        result["success"] = True
    except Exception as e:
        result["errors"].append(str(e))
    return result


def handle_define_batch(post_data, user, schema_obj):
    result = {"data": {}, "success": False, "errors": []}
    try:
        if not core.utils.samples.check_if_empty_data(post_data):
            sample_saved = core.utils.samples.get_sample_pre_recorded(user)
            m_batch_form = core.utils.samples.create_form_for_batch(schema_obj, user)
            result["data"] = {"m_batch_form": m_batch_form, "sample_saved": sample_saved}
            result["success"] = True
            return result
        meta_data = core.utils.samples.join_sample_and_batch(post_data, user, schema_obj)
        core.utils.samples.write_form_data_to_excel(meta_data, user)
        core.utils.samples.delete_temporary_sample_table(user)
        result["data"] = {"sample_recorded": {"ok": "OK"}}
        result["success"] = True
    except Exception as e:
        result["errors"].append(str(e))
    return result


def get_metadata_form_initial(user, schema_obj):
    result = {"data": {}, "success": True, "errors": []}
    try:
        if core.utils.samples.pending_samples_in_metadata_form(user):
            sample_saved = core.utils.samples.get_sample_pre_recorded(user)
            m_batch_form = core.utils.samples.create_form_for_batch(schema_obj, user)
            result["data"] = {"m_batch_form": m_batch_form, "sample_saved": sample_saved}
            return result
        m_form = core.utils.samples.create_metadata_form(schema_obj, user)
        if "ERROR" in m_form:
            result["success"] = False
            result["errors"].append(m_form["ERROR"])
            return result
        if 'None' in m_form["lab_name"] or m_form["lab_name"] == "":
            result["success"] = False
            result["errors"].append(core.config.ERROR_USER_IS_NOT_ASSIGNED_TO_LAB)
            return result
        result["data"] = {"m_form": m_form}
    except Exception as e:
        result["success"] = False
        result["errors"].append(str(e))
    return result
