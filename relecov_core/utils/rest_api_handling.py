import json
from relecov_tools.rest_api import RestApi
from relecov_core.utils.generic_functions import get_configuration_value
from relecov_core.core_config import (
    ISKLIMS_GET_LABORATORY_PARAMETERS,
    ISKLIMS_PUT_LABORATORY_PARAMETER,
    ISKLIMS_REST_API,
    ISKLIMS_GET_SAMPLE_FIELDS,
    ISKLIMS_GET_SAMPLE_INFORMATION,
    ISKLIMS_GET_SAMPLE_PROJECT_FIELDS,
    ISKLIMS_GET_SUMMARIZE_DATA,
    ISKLIMS_POST_SAMPLE_DATA,
)


def create_get_api_instance(request_param, data):
    """Crate api request to iSkyLIMS"""
    iskylims_server = get_configuration_value("ISKYLIMS_SERVER")
    iskylims_url = ISKLIMS_REST_API
    request, param = request_param
    r_api = RestApi(iskylims_server, iskylims_url)
    return r_api.get_request(request, param, data)


def get_laboratory_data(lab_name):
    """Send api request to iSkyLIMS to fetch laboratory data"""

    iskylims_server = get_configuration_value("ISKYLIMS_SERVER")
    iskylims_url = ISKLIMS_REST_API
    request, param = ISKLIMS_GET_LABORATORY_PARAMETERS
    r_api = RestApi(iskylims_server, iskylims_url)
    data = r_api.get_request(request, param, lab_name)
    if "ERROR" in data:
        return {"ERROR": data}
    return data


def set_laboratory_data(lab_data):
    """Send api request to iSkyLIMS to update laboratory data"""

    iskylims_server = get_configuration_value("ISKYLIMS_SERVER")
    iskylims_url = ISKLIMS_REST_API

    request = ISKLIMS_PUT_LABORATORY_PARAMETER
    r_api = RestApi(iskylims_server, iskylims_url)
    data = r_api.put_request(request, lab_data)
    if "ERROR" in data:
        return {"ERROR": data}
    return data


def get_sample_fields_data():
    """Send API request to iSkyLIMs to get the sample_fields and their options"""
    iskylims_server = get_configuration_value("ISKYLIMS_SERVER")
    iskylims_url = ISKLIMS_REST_API
    request = ISKLIMS_GET_SAMPLE_FIELDS
    r_api = RestApi(iskylims_server, iskylims_url)
    data = r_api.get_request(request, "", "")
    if "ERROR" in data:
        return {"ERROR": data}
    return data["DATA"]


def get_sample_information(sample_name):
    """Send APY request to iSkyLIMS to get sample and sample project information"""
    """
    iskylims_server = get_configuration_value("ISKYLIMS_SERVER")
    iskylims_url = ISKLIMS_REST_API
    request = ISKLIMS_GET_SAMPLE_INFORMATION
    r_api = RestApi(iskylims_server, iskylims_url)
    """
    data = create_get_api_instance(ISKLIMS_GET_SAMPLE_INFORMATION, sample_name)
    # data = r_api.get_request(request, sample_name)
    if "ERROR" in data:
        return {"ERROR": data}
    return data["DATA"]


def get_sample_project_fields_data(project):
    """Send API request to iSkyLIMS to get the sample project fields and their
    options
    """
    iskylims_server = get_configuration_value("ISKYLIMS_SERVER")
    iskylims_url = ISKLIMS_REST_API
    request, param = ISKLIMS_GET_SAMPLE_PROJECT_FIELDS
    r_api = RestApi(iskylims_server, iskylims_url)
    data = r_api.get_request(request, param, project)
    if "ERROR" in data:
        return {"ERROR": data}
    return data["DATA"]


def get_summarize_data(param_data):
    """Send API request to iSkyLIMS to get the summarize data options"""
    iskylims_server = get_configuration_value("ISKYLIMS_SERVER")
    iskylims_url = ISKLIMS_REST_API
    request = ISKLIMS_GET_SUMMARIZE_DATA
    r_api = RestApi(iskylims_server, iskylims_url)
    data = r_api.get_request(request, param_data)
    if "ERROR" in data:
        return {"ERROR": data}
    return data["DATA"]


def save_sample_form_data(post_data, credencials):
    """Send POST API request to iSkyLIMS to save sample data"""
    iskylims_server = get_configuration_value("ISKYLIMS_SERVER")
    iskylims_url = ISKLIMS_REST_API
    request = ISKLIMS_POST_SAMPLE_DATA
    r_api = RestApi(iskylims_server, iskylims_url)

    data = r_api.post_request(json.dumps(post_data), credencials, request)
    if "ERROR" in data:
        return data
    return data["DATA"]
