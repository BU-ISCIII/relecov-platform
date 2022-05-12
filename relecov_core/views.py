from relecov_core.utils.generic_functions import store_file
# from relecov_core.utils.metadata_handling import upload_excel_file

from relecov_core.utils.handling_samples import (
    create_metadata_form,
    analyze_input_samples,
)
from relecov_core.utils.metadata_handling import upload_excel_file

from relecov_core.utils.schema_handling import (
    process_schema_file,
    get_schemas_loaded,
    get_schema_display_data,
)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, "relecov_core/index.html", {})


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

        return render(
            request,
            "relecov_core/schemaHandling.html",
            {"SUCCESS": schema_data["SUCCESS"]},
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
def intranet(request):
    return render(request, "relecov_core/intranet2.html")


def variants(request):
    return render(request, "relecov_core/variants.html", {})


def documentation(request):
    return render(request, "relecov_core/documentation.html", {})


@login_required()
def metadata_form(request):
    m_form = create_metadata_form()
    """
    if request.method == "POST" and request.POST["action"] == "metadata_form_batch":
        sample_recorded = {}
        sample_recorded = m_form
        sample_recorded["process"] = "pre_metadata_is_correct"
        return render(
            request,
            "relecov_core/metadataForm2.html",
            {"sample_recorded": sample_recorded},
        )
    """
    if request.method == "POST" and request.POST["action"] == "sampledefinition":
        sample_recorded = analyze_input_samples(request)
        # import pdb; pdb.set_trace()
        return render(
            request,
            "relecov_core/metadataForm2.html",
            {"sample_recorded": sample_recorded},
        )
    elif request.method == "POST" and request.POST["action"] == "defineBatchSamples":
        print("Fichero recibido")
        # uploadedFile = request.FILES["samplesExcel"]
        # path_file = store_file(request.FILES["samplesExcel"],"2022_5_10")
        # print(path_file)
        sample_recorded = upload_excel_file(request)

    return render(request, "relecov_core/metadataForm2.html", {"m_form": m_form})


@login_required()
def contributor_info(request):
    if request.method == "POST":
        print(request.POST["hospital_name"])
        print(request.POST)
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
