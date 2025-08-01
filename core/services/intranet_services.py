import core.serializers
import core.utils.samples
import core.utils.public_db
import core.utils.bioinfo_analysis
import core.utils.utils
from . import get_lab_name_from_user


def get_intranet_data_for_manager():
    """Collect dashboard data for the manager intranet view."""
    result = {"data": {}, "success": False, "errors": []}
    try:
        all_sample_per_date = core.utils.samples.get_sample_per_date_per_all_lab()
        num_of_samples = core.utils.samples.count_handled_samples()
        analysis_percent = core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab()

        bar_config = {
            "col_names": ["Sequencing Date", "Number of samples"],
            "options": {"title": "Samples Received for all laboratories", "width": 590},
        }

        # dash graph for samples per lab
        core.utils.samples.create_dash_bar_for_each_lab()

        gisaid_raw = core.utils.public_db.get_public_accession_from_sample_lab("gisaid_accession_id")
        ena_raw = core.utils.public_db.get_public_accession_from_sample_lab("ena_sample_accession")
        actions_raw = core.utils.samples.get_lab_last_actions()

        data = {
            "sample_bar_graph": core.utils.samples.create_date_sample_bar(all_sample_per_date, bar_config),
            "sample_gauge_graph": core.utils.utils.perc_gauge_graphic(analysis_percent),
            "actions": core.serializers.LabLastActionSerializer.from_raw(actions_raw),
        }

        if gisaid_raw:
            data["gisaid_accession"] = core.serializers.PublicAccessionSerializer.from_raw(gisaid_raw)
            data["gisaid_graph"] = core.utils.public_db.percentage_graphic(
                num_of_samples.get("Defined", 0), len(gisaid_raw), ""
            )
        if ena_raw:
            data["ena_accession"] = core.serializers.PublicAccessionSerializer.from_raw(ena_raw)
            data["ena_graph"] = core.utils.public_db.percentage_graphic(
                num_of_samples.get("Defined", 0), len(ena_raw), ""
            )

        result["data"] = data
        result["success"] = True
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result


def get_intranet_data_for_user(user):
    """Collect dashboard data for a regular user."""
    result = {"data": {}, "success": False, "errors": []}
    try:
        lab_name = get_lab_name_from_user(user)
        date_lab_samples = core.utils.samples.get_sample_per_date_per_lab(lab_name)
        if not date_lab_samples:
            result["errors"].append({"code": 404, "message": f"No samples found for selected laboratory: {lab_name}"})
            return result

        sample_lab_objs = core.utils.samples.get_sample_objs_per_lab(lab_name)
        analysis_percent = core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab(lab_name)

        bar_config = {
            "col_names": ["Sequencing Date", "Number of samples"],
            "options": {"title": "Samples Received", "width": 600},
        }

        gisaid_raw = core.utils.public_db.get_public_accession_from_sample_lab(
            "gisaid_accession_id", sample_lab_objs
        )
        ena_raw = core.utils.public_db.get_public_accession_from_sample_lab(
            "ena_sample_accession", sample_lab_objs
        )
        actions_raw = core.utils.samples.get_lab_last_actions(lab_name)

        data = {
            "sample_bar_graph": core.utils.samples.create_date_sample_bar(date_lab_samples, bar_config),
            "sample_gauge_graph": core.utils.utils.perc_gauge_graphic(analysis_percent),
            "actions": core.serializers.LabLastActionDictSerializer.from_raw(actions_raw),
        }

        if gisaid_raw:
            data["gisaid_accession"] = core.serializers.PublicAccessionSerializer.from_raw(gisaid_raw)
            data["gisaid_graph"] = core.utils.public_db.percentage_graphic(
                len(sample_lab_objs), len(gisaid_raw), ""
            )
        if ena_raw:
            data["ena_accession"] = core.serializers.PublicAccessionSerializer.from_raw(ena_raw)
            data["ena_graph"] = core.utils.public_db.percentage_graphic(
                len(sample_lab_objs), len(ena_raw), ""
            )

        result["data"] = data
        result["success"] = True
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result
