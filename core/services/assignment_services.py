import core.config
import core.models
import core.serializers
import core.utils.labs as labs_utils


def _get_defined_users():
    """Return list of [id, username] for all users except admin."""
    user_list = []
    user_objs = core.models.User.objects.all().exclude(username__iexact="admin").order_by("username")
    for user_obj in user_objs:
        user_list.append([user_obj.pk, user_obj.username])
    return user_list


def handle_assign_samples_to_user(action=None, post_data=None, user=None):
    """Assign samples belonging to a lab to a given user."""
    result = {"data": {}, "success": False, "errors": []}
    labs = labs_utils.get_all_defined_labs()
    users = _get_defined_users()

    if isinstance(labs, dict) and "ERROR" in labs:
        result["errors"].append({"code": 500, "message": labs.get("ERROR", "Error loading labs")})
        return result

    if action == "assignSamples":
        lab = post_data.get("lab") if post_data else None
        user_id = post_data.get("userName") if post_data else None
        if not user_id:
            result["errors"].append({"code": 400, "message": "No user selected."})
        else:
            try:
                user_obj = core.models.User.objects.get(pk=user_id)
                samples_qs = core.models.Sample.objects.filter(collecting_institution__iexact=lab)
                if samples_qs.exists():
                    samples_qs.update(user=user_obj)
                    result["data"] = core.serializers.LabUserAssignSerializer.from_raw_data(
                        labs, users, SUCCESS="Samples reassigned."
                    )
                    result["success"] = True
                else:
                    result["errors"].append({
                        "code": 404,
                        "message": f"{core.config.ERROR_NO_SAMPLES_ARE_ASSIGNED_TO_LAB} {lab}",
                    })
            except core.models.User.DoesNotExist:
                result["errors"].append({
                    "code": 404,
                    "message": f"User with ID {user_id} does not exist.",
                })
    else:
        result["data"] = core.serializers.LabUserAssignSerializer.from_raw_data(labs, users)
        result["success"] = True
    return result
