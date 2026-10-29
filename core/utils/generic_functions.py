# Generic imports
import time
import os
from datetime import datetime, timedelta
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User

# local imports
import core.models
import core.config


def get_configuration_value(parameter_name):
    """
    Description:
        Function will get the parameter value defined in the configutration table
        if not exists return 'False'

    Input:
        parameter_name    #parameter name
    Return:
        parameter_value
    """

    parameter_value = "False"
    if core.models.ConfigSetting.objects.filter(
        configuration_name__exact=parameter_name
    ).exists():
        parameter_obj = core.models.ConfigSetting.objects.filter(
            configuration_name__exact=parameter_name
        ).last()
        parameter_value = parameter_obj.get_configuration_value()
    return parameter_value


def get_defined_users():
    """Get the id and the user names defined in relecov"""
    user_list = []
    user_objs = (
        User.objects.all().exclude(username__iexact="admin").order_by("username")
    )
    for user_obj in user_objs:
        user_list.append([user_obj.pk, user_obj.username])
    return user_list


def store_file(user_file, folder):
    """
    Description:
        The function save the user input file
    Input:
        user_file # contains the file
        folder      subfolder to store the file
    Return:
        file_name
    """
    filename, file_extension = os.path.splitext(user_file.name)
    file_name = filename + "_" + str(time.strftime("%Y%m%d-%H%M%S")) + file_extension
    store_filepath = os.path.join(folder, file_name)
    fs = FileSystemStorage()
    fs.save(store_filepath, user_file)
    return store_filepath


def check_valid_date_format(date):
    """check it date has a valid format"""
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def list_all_possible_weeks(min_date, max_date, output_format=""):
    """Generate a list of all weeks in date or string format between min_date and max_date

    Args:
        min_date (datetime): starting date
        max_date (datetime): last date
        date_format (str, optional): Return dates as strings instead of dates
        in output format. Defaults to "". e.g. "%Y-W%V"

    Returns:
        all_dates: list of dates between starting and end date, one per week
    """
    all_dates = []
    current_date = min_date
    if output_format:
        while current_date <= max_date:
            all_dates.append(current_date.strftime(output_format))
            current_date += timedelta(weeks=1)
    else:
        while current_date <= max_date:
            all_dates.append(current_date)
            current_date += timedelta(weeks=1)
    return all_dates


def get_user_role(user):
    """Return the highest hierarchical group for the user"""
    user_groups = user.groups.values_list("name", flat=True)
    hierarchy = core.config.GROUPS_HIERARCHY_ORDERLIST
    for group in hierarchy:
        if group in user_groups:
            return group
    else:
        return None


def get_user_lab_field(user):
    user_group = get_user_role(user)
    return core.config.INSTITUTION_FIELD_MAPDICT.get(user_group)


def cookie_consent(request):
    has_cookie_consent = core.config.COOKIE_CONSENT_NAME in request.COOKIES
    return {
        "show_cookie_banner": not has_cookie_consent,
        "show_cookie_settings": False,
        "cookie_settings_tab": "privacy",
        "cookie_consent_next": request.path,
    }
