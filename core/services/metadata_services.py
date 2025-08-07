import json

import core.config
import core.models
import core.serializers
import core.utils.schema
import core.utils.samples


def _handle_metadata_upload(metadata_file, username):
    """Store uploaded metadata file into Samba."""
    result = {"data": {}, "success": False, "errors": []}
    try:
        core.utils.samples.save_excel_form_in_samba_folder(metadata_file, username)
        result["data"] = {"sample_recorded": {"ok": "OK"}}
        result["success"] = True
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result


def _handle_define_samples(post_data, user, schema_obj):
    """Process the form for defining samples."""
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
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result


def _handle_define_batch(post_data, user, schema_obj):
    """Handle metadata batch definition."""
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
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result


def _get_metadata_form_initial(user, schema_obj):
    """Return the initial data to display the metadata form."""
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
            result["errors"].append({"code": 500, "message": m_form["ERROR"]})
            return result
        if "None" in m_form["lab_name"] or m_form["lab_name"] == "":
            result["success"] = False
            result["errors"].append({"code": 400, "message": core.config.ERROR_USER_IS_NOT_ASSIGNED_TO_LAB})
            return result
        result["data"] = {"m_form": m_form}
    except Exception as exc:
        result["success"] = False
        result["errors"].append({"code": 500, "message": str(exc)})
    return result


def handle_metadata_form(action=None, post_data=None, files=None, user=None, schema_obj=None):
    """Central entry point for metadata form actions."""
    if action == "uploadMetadataFile" and files:
        response = _handle_metadata_upload(files.get("metadataFile"), user.username)
    elif action == "defineSamples":
        response = _handle_define_samples(post_data, user, schema_obj)
    elif action == "defineBatch":
        response = _handle_define_batch(post_data, user, schema_obj)
    else:
        response = _get_metadata_form_initial(user, schema_obj)

    mapped_data = {}
    source = response.get("data", {})
    if "m_form" in source:
        mapped_data["DATA_FORM"] = source["m_form"]
    if "sample_issues" in source:
        mapped_data["DATA_SAMPLEISSUES"] = source["sample_issues"]
    if "m_batch_form" in source:
        mapped_data["DATA_BATCHFORM"] = source["m_batch_form"]
    if "sample_saved" in source:
        mapped_data["DATA_SAMPLESAVED"] = source["sample_saved"]
    if "sample_recorded" in source:
        mapped_data["DATA_SAMPLERECORDED"] = source["sample_recorded"]

    return {
        "data": mapped_data,
        "success": response.get("success"),
        "errors": response.get("errors"),
    }


def get_metadata_visualization_data(schema):
    data = {"sample": [], "batch": []}
    for fill_mode in ["sample", "batch"]:
        qs = core.models.MetadataVisualization.objects.filter(
            schemaID=schema, fill_mode=fill_mode, in_use=True
        ).order_by("order")
        data[fill_mode] = core.serializers.MetadataVisualizationSerializer(
            qs, many=True
        ).data
    return data


def store_metadata_visualization_fields(schema_id, fields, fill_mode="sample"):
    core.models.MetadataVisualization.objects.filter(
        schemaID=schema_id, fill_mode=fill_mode
    ).delete()
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


def handle_metadata_visualization(request):
    action = request.POST.get("action") if request.method == "POST" else None
    table_data_json = request.POST.get("tableData") if request.method == "POST" else None

    result = {"data": None, "success": None, "errors": []}
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
            except Exception as exc:
                result["success"] = False
                result["errors"].append(f"Error parsing table_data: {exc}")
                return result

            core.models.MetadataVisualization.objects.filter(schemaID=schema).delete()
            for row in rows:
                core.models.MetadataVisualization.objects.create(
                    schemaID=schema,
                    property_name=row[0],
                    label_name=row[1],
                    order=(row[2] if row[2] != "" else 0),
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

        visualization = get_metadata_visualization_data(schema)
        if visualization["sample"] or visualization["batch"]:
            result["data"] = {"visualization": visualization}
        else:
            template_labels = core.utils.schema.get_fields_if_template()
            result["data"] = {
                "schema_fields": get_schema_fields_for_jexcel(schema, template_labels)
            }
        result["success"] = True
    except Exception as exc:
        result["success"] = False
        result["errors"].append(str(exc))
    return result
