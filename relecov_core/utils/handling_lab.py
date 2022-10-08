from relecov_core.models import Profile


def get_lab_name(user_obj):
    """Get the laboratory name for the user"""
    if Profile.objects.filter(user=user_obj).exists():
        profile_obj = Profile.objects.filter(user=user_obj).last()
        return profile_obj.get_lab_name()
    else:
        return ""
