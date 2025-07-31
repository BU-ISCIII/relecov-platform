import core.models
import core.serializers as serializers_module
import core.utils.schema as schema_utils
import core.config


class SchemaError(Exception):
    """Custom exception for schema operations"""
    pass


def _process_schema_file(schema_file, default_flag, user, app_name):
    try:
        data = schema_utils.process_schema_file(schema_file, default_flag, user, app_name)
    except Exception as exc:
        raise SchemaError(str(exc))
    if isinstance(data, dict) and "ERROR" in data:
        raise SchemaError(data["ERROR"])
    return data


def _get_loaded_schemas(app_name):
    try:
        return core.models.Schema.objects.filter(
            schema_apps_name__exact=app_name
        ).order_by("schema_name")
    except Exception as exc:
        raise SchemaError(str(exc))


def handle_schema_upload(action, schema_file, default_flag, user, app_name):
    result = {"data": {}, "success": False, "errors": []}
    try:
        if action == "uploadSchema" and schema_file:
            upload_data = _process_schema_file(schema_file, default_flag, user, app_name)
            result["data"]["message"] = upload_data.get("SUCCESS")
        schemas_qs = _get_loaded_schemas(app_name)
        result["data"]["schemas"] = serializers_module.SchemaListSerializer(
            schemas_qs, many=True
        ).data
        result["success"] = True
    except SchemaError as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    result["success"] = len(result["errors"]) == 0 and result.get("success", False) or result.get("success", False)
    return result


def get_loaded_schemas(app_name):
    result = {"data": {}, "success": False, "errors": []}
    try:
        schemas_qs = _get_loaded_schemas(app_name)
        result["data"]["schemas"] = serializers_module.SchemaListSerializer(
            schemas_qs, many=True
        ).data
        result["success"] = True
    except SchemaError as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result


def get_schema_display(schema_id):
    """Return schema properties data for display"""
    result = {"data": {}, "success": False, "errors": []}
    try:
        schema = schema_utils.get_schema_obj_from_id(schema_id)
        if not schema:
            result["errors"].append(
                {"code": 404, "message": core.config.ERROR_SCHEMA_ID_NOT_DEFINED}
            )
            return result

        props_qs = core.models.SchemaProperties.objects.filter(
            schemaID=schema
        ).order_by("property")
        result["data"] = {
            "heading": core.config.HEADING_SCHEMA_DISPLAY,
            "schema": serializers_module.SchemaPropertyDisplaySerializer(
                props_qs, many=True
            ).data,
        }
        result["success"] = True
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result
