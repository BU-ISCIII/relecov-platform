from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from relecov_core.utils.handling_samples import (
    analyze_input_samples,
    create_metadata_form,
    get_sample_display_data,
    get_search_data,
    save_temp_sample_data,
    search_samples,
)

from relecov_core.utils.schema_handling import (
    del_metadata_visualization,
    fetch_info_meta_visualization,
    get_schemas_loaded,
    get_schema_obj_from_id,
    get_schema_display_data,
    get_latest_schema,
    get_fields_from_schema,
    process_schema_file,
    store_fields_metadata_visualization,
)

from relecov_core.utils.bio_info_json_handling import process_bioinfo_file
from relecov_core.utils.contributor_info_handling import get_data_from_form
from relecov_core.utils.generic_functions import check_valid_date_format

from relecov_core.models import Sample
from relecov_core.core_config import (
    ERROR_USER_FIELD_DOES_NOT_ENOUGH_CHARACTERS,
    ERROR_INVALID_DEFINED_SAMPLE_FORMAT,
    ERROR_NOT_MATCHED_ITEMS_IN_SEARCH,
    HEADING_FOR_SAMPLE_LIST,
)


def index(request):
    number_of_samples_received = Sample.objects.count()
    return render(
        request,
        "relecov_core/index.html",
        {"number_of_samples_received": number_of_samples_received},
    )


@login_required
def bio_info_json_handling(request):
    if request.method == "POST" and request.POST["action"] == "uploadBioInfo":
        bioinfo_data = process_bioinfo_file(
            request.FILES["BioInfoFile"],
            request.user,
            __package__,
        )
        print(bioinfo_data)

        """
        if "ERROR" in schema_data:
            return render(
                request,
                "relecov_core/bioInfoJSONHandling.html",
                {"ERROR": schema_data["ERROR"]},
            )

        return render(
            request,
            "relecov_core/bioInfoJSONHandling.html",
            {"SUCCESS": bioinfo_data["SUCCESS"]},
        )
        """
    # schemas = get_schemas_loaded(__package__)
    """
    return render(
        request, "relecov_core/bioInfoJSONHandling.html", {"schemas": schemas}
    )
    """
    # test flake new test
    return render(request, "relecov_core/bioInfoJSONHandling.html", {})


@login_required
def sample_display(request, sample_id):
    sample_data = get_sample_display_data(sample_id, request.user)
    if "ERROR" in sample_data:
        return render(
            request, "relecov_core/sampleDisplay.html", {"ERROR": sample_data["ERROR"]}
        )
    return render(
        request, "relecov_core/sampleDisplay.html", {"sample_data": sample_data}
    )


@login_required
def schema_handling(request):
    if request.user.username != "admin":
        return redirect("/")
    if request.method == "POST" and request.POST["action"] == "uploadSchema":
        schema_data = process_schema_file(
            request.FILES["schemaFile"],
            request.POST["schemaVersion"],
            request.POST["schemaDefault"],
            request.user,
            __package__,
        )
        if "ERROR" in schema_data:
            return render(
                request,
                "relecov_core/schemaHandling.html",
                {"ERROR": schema_data["ERROR"]},
            )
        schemas = get_schemas_loaded(__package__)
        return render(
            request,
            "relecov_core/schemaHandling.html",
            {"SUCCESS": schema_data["SUCCESS"], "schemas": schemas},
        )
    schemas = get_schemas_loaded(__package__)
    return render(request, "relecov_core/schemaHandling.html", {"schemas": schemas})


@login_required
def schema_display(request, schema_id):
    if request.user.username != "admin":
        return redirect("/")
    schema_data = get_schema_display_data(schema_id)
    return render(
        request, "relecov_core/schemaDisplay.html", {"schema_data": schema_data}
    )


@login_required
def search_sample(request):
    """Search sample using the filter in the form"""
    search_data = get_search_data()
    if request.method == "POST" and request.POST["action"] == "searchSample":
        sample_name = request.POST["sampleName"]
        s_date = request.POST["sDate"]
        user_name = request.POST["userName"]
        sample_state = request.POST["sampleState"]
        # check that some values are in the request if not return the form
        if (
            user_name == ""
            and s_date == ""
            and sample_name == ""
            and sample_state == ""
        ):
            return render(
                request, "relecov_core/searchSample.html", {"search_data": search_data}
            )
        if user_name != "" and len(user_name) < 5:
            return render(
                request,
                "relecov_core/searchSample.html",
                {
                    "search_data": search_data,
                    "warning": ERROR_USER_FIELD_DOES_NOT_ENOUGH_CHARACTERS,
                },
            )
        # check the right format of s_date
        if s_date != "" and not check_valid_date_format(s_date):
            return render(
                request,
                "relecov_core/searchSample.html",
                {
                    "search_data": search_data,
                    "warning": ERROR_INVALID_DEFINED_SAMPLE_FORMAT,
                },
            )
        sample_list = search_samples(sample_name, user_name, sample_state, s_date)
        if len(sample_list) == 0:
            return render(
                request,
                "relecov_core/searchSample.html",
                {
                    "search_data": search_data,
                    "warning": ERROR_NOT_MATCHED_ITEMS_IN_SEARCH,
                },
            )
        if len(sample_list) == 1:
            return redirect("display_sample", sample_id=sample_list)
        else:
            sample = {"s_data": sample_list, "heading": HEADING_FOR_SAMPLE_LIST}
            return render(
                request, "relecov_core/searchSample.html", {"list_display": sample}
            )
    # import pdb; pdb.set_trace()
    if "ERROR" in search_data:
        return render(
            request, "relecov_core/searchSample.html", {"ERROR": search_data["ERROR"]}
        )
    return render(
        request, "relecov_core/searchSample.html", {"search_data": search_data}
    )


@login_required
def metadata_visualization(request):
    if request.user.username != "admin":
        return redirect("/")
    if request.method == "POST" and request.POST["action"] == "selectFields":
        selected_fields = store_fields_metadata_visualization(request.POST)
        if "ERROR" in selected_fields:
            m_visualization = get_fields_from_schema(
                get_schema_obj_from_id(request.POST["schemaID"])
            )
            return render(
                request,
                "relecov_core/metadataVisualization.html",
                {"ERROR": selected_fields, "m_visualization": m_visualization},
            )
        return render(
            request,
            "relecov_core/metadataVisualization.html",
            {"SUCCESS": selected_fields},
        )
    if request.method == "POST" and request.POST["action"] == "deleteFields":
        del_metadata_visualization()
        return render(
            request, "relecov_core/metadataVisualization.html", {"DELETE": "DELETE"}
        )
    metadata_obj = get_latest_schema("Relecov", __package__)
    if isinstance(metadata_obj, dict):
        return render(
            request,
            "relecov_core/metadataVisualization.html",
            {"ERROR": metadata_obj["ERROR"]},
        )
    data_visualization = fetch_info_meta_visualization(metadata_obj)
    if isinstance(data_visualization, dict):
        return render(
            request,
            "relecov_core/metadataVisualization.html",
            {"data_visualization": data_visualization},
        )
    m_visualization = get_fields_from_schema(metadata_obj)
    return render(
        request,
        "relecov_core/metadataVisualization.html",
        {"m_visualization": m_visualization},
    )


@login_required
def intranet(request):
    return render(request, "relecov_core/intranet.html")


def variants(request):
    return render(request, "relecov_core/variants.html", {})


@login_required()
def metadata_form(request):
    schema_obj = get_latest_schema("relecov", __package__)
    m_form = create_metadata_form(schema_obj, request.user)
    if "ERROR" in m_form:
        return render(
            request, "relecov_core/metadataForm.html", {"ERROR": m_form["ERROR"]}
        )
    if request.method == "POST" and request.POST["action"] == "defineSamples":
        res_analyze = analyze_input_samples(request)
        # empty form
        if len(res_analyze) == 0:
            return render(request, "relecov_core/metadataForm.html", {"m_form": m_form})
        if "save_samples" in res_analyze:
            s_saved = save_temp_sample_data(res_analyze["save_samples"])
        if "s_incomplete" in res_analyze:
            return render(
                request,
                "relecov_core/metadataForm.html",
                {"s_incomplete": res_analyze["s_incomplete"], "m_form": m_form},
            )
        return render(request, "relecov_core/metadataForm.html", {"s_saved": s_saved})
    if request.method == "POST" and request.POST["action"] == "defineBatch":
        pass
    else:
        if "ERROR" in m_form:
            return render(
                request, "relecov_core/metadataForm.html", {"ERROR": m_form["ERROR"]}
            )
        return render(request, "relecov_core/metadataForm.html", {"m_form": m_form})


@login_required()
def contributor_info(request):
    if request.method == "POST":
        contributor_info_dict = get_data_from_form(request)
        print(contributor_info_dict)
    return render(request, "relecov_core/contributorInfo.html", {})


@login_required()
def upload_status(request):
    return render(request, "relecov_core/uploadStatus.html", {})


@login_required()
def upload_status_to_ENA(request):
    return render(request, "relecov_core/uploadStatusToENA.html", {})


@login_required()
def upload_status_to_GISAID(request):
    return render(request, "relecov_core/uploadStatusToGISAID.html", {})


@login_required()
def results_info_received(request):
    return render(request, "relecov_core/resultsInfoReceived.html", {})


@login_required()
def results_info_processed(request):
    return render(request, "relecov_core/resultsInfoProcessed.html", {})


@login_required()
def results_download(request):
    return render(request, "relecov_core/resultsDownload.html", {})


# @login_required()


def contact(request):
    return render(request, "relecov_core/contact.html", {})


# @login_required()


def relecov_project(request):
    return render(request, "relecov_core/relecov_project.html", {})
