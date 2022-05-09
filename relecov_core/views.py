from datetime import datetime

# import os

# Important! ==>  pip install xlrd==1.2.0
import xlrd

# from relecov_core.models import Document

from relecov_core.utils.handling_samples import (
    get_input_samples,
    analyze_input_samples,
)

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
    sample_recorded = get_input_samples()
    if request.method == "POST":
        sample_recorded["process"] = "pre_metadata_is_correct"
        return render(
            request,
            "relecov_core/metadataForm2.html",
            {"sample_recorded": sample_recorded},
        )
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
        date = datetime.today().strftime("%Y-%m-%d_%H:%M")
        user_name = request.user.username
        title = "metadata_{}_{}".format(user_name, date)
        # file_path = datetime.today().strftime("%Y_%m_%d")
        print(title)

        # Fetching the form data
        # uploadedFile = request.FILES["samplesExcel"]
        # Create a folder per day if it doesn't exist
        # path = os.path.join(METADATA_UPLOAD_FOLDER, file_path)
        # if not os.path.exists(path):
        #    os.mkdir(path)

        # Saving the information in the database
        # file_upload = store_file(uploadedFile, path)
        # documents = Document.objects.all()

        # read excel file xlrd example
        book = xlrd.open_workbook(
            "documents/metadata/2022_05_08/METADATA_LAB_RESPIRATORIOS_V2.xlsx"
        )
        print("The number of worksheets is {0}".format(book.nsheets))
        print("Worksheet name(s): {0}".format(book.sheet_names()))
        sh = book.sheet_by_index(1)
        print("{0} {1} {2}".format(sh.name, sh.nrows, sh.ncols))
        print("Cell D30 is {0}".format(sh.cell_value(rowx=29, colx=3)))
        # for rx in range(sh.nrows):
        #    print(type(sh.row(rx)))

        print(type(sh.row(0)))
        print(sh.row(0))
        sample_recorded["Process"] = "fichero_recibido"
        return render(
            request,
            "relecov_core/metadataForm2.html",
            {"sample_recorded": "sample_recorded"},
        )

    return render(
        request, "relecov_core/metadataForm2.html", {"sample_recorded": sample_recorded}
    )


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
