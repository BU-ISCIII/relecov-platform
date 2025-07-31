from . import get_search_data, validate_search_params, display_samples


def handle_sample_search(action=None, sample_name="", s_date="", lab_name="", sample_state="", user=None):
    """Orchestrate sample search workflow."""
    result = {"data": {}, "success": False, "errors": []}

    # Always include form data
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
