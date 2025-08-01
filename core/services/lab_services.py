import core.utils.labs as labs_utils


def handle_laboratory_contact(action=None, post_data=None, user=None):
    """Retrieve or update laboratory contact information."""
    result = {"data": {}, "success": False, "errors": []}
    try:
        lab_data = labs_utils.get_lab_contact_details(user)
        if isinstance(lab_data, str):
            result["errors"].append({"code": 500, "message": lab_data or "No laboratory data"})
            return result

        if action == "updateLabData" and post_data is not None:
            update_result = labs_utils.update_contact_lab(lab_data, post_data)
            if isinstance(update_result, dict):
                result["errors"].append({"code": 500, "message": update_result.get("ERROR")})
                return result
            result["data"]["message"] = "Success"

        result["data"]["lab_data"] = lab_data
        result["success"] = len(result["errors"]) == 0
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result
