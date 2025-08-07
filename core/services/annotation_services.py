"""Services for organism annotations."""

from typing import Optional

import core.utils.annotation


def get_annotation_details(annot_id: int) -> dict:
    """Retrieve annotation detail data."""
    result = {"data": {}, "success": False, "errors": []}
    try:
        if not core.utils.annotation.check_if_annotation_exists(annot_id):
            result["errors"].append(
                {"code": 404, "message": "Annotation does not exist"}
            )
            return result
        annot_data = core.utils.annotation.get_annotation_data(annot_id)
        result["data"]["annotation_data"] = annot_data
        result["success"] = True
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result


def handle_organism_annotation(
    action: Optional[str], *, gff_file=None, user=None
) -> dict:
    """Handle organism annotation upload and retrieval."""
    result = {"data": {}, "success": False, "errors": []}
    try:
        annotations = core.utils.annotation.get_annotations()
        result["data"]["annotations"] = annotations

        if action == "uploadAnnotation":
            if not gff_file:
                result["errors"].append(
                    {"code": 400, "message": "No file provided"}
                )
                return result
            gff_parsed = core.utils.annotation.read_gff_file(gff_file)
            if "ERROR" in gff_parsed:
                result["errors"].append({"code": 400, "message": gff_parsed["ERROR"]})
                return result
            core.utils.annotation.store_gff(gff_parsed, user)
            result["data"]["annotations"] = core.utils.annotation.get_annotations()
            result["success"] = True
            return result

        result["success"] = True
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result
