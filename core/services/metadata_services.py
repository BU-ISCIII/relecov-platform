import core.utils.samples
import core.config


def handle_metadata_upload(metadata_file, username):
    """Store uploaded metadata file into Samba."""
    result = {"data": {}, "success": False, "errors": []}
    try:
        core.utils.samples.save_excel_form_in_samba_folder(metadata_file, username)
        result["data"] = {"sample_recorded": {"ok": "OK"}}
        result["success"] = True
    except Exception as exc:
        result["errors"].append({"code": 500, "message": str(exc)})
    return result


def handle_define_samples(post_data, user, schema_obj):
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


def handle_define_batch(post_data, user, schema_obj):
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


def get_metadata_form_initial(user, schema_obj):
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
