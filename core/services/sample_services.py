from . import get_search_data, validate_search_params, display_samples

import core.utils.samples_map
import core.utils.samples_graphics


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
        sample_data["received_samples_graph"] = (
            core.utils.samples_graphics.received_samples_graph()
        )
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
