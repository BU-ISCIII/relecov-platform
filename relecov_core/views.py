from datetime import datetime
import os
from pathlib import Path
#import pandas as pd

import xlrd # Important! ==>  pip install xlrd==1.2.0
from relecov_core.models import Document, document_path_folder

from relecov_core.utils.handling_samples import (
    get_input_samples,
    analyze_input_samples,
)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


def index(request):
    return render(request, "relecov_core/index.html", {})


@login_required
def schema_handling(request):
    if request.user.username != "admin":
        return redirect("/")
    return render(request, "relecov_core/schemaHandling.html")


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
        file_path = datetime.today().strftime("%Y_%m_%d")
        print(title)

        # Fetching the form data
        uploadedFile = request.FILES["samplesExcel"]
        # Create a folder per day if it doesn't exist  
        path = os.path.join("documents/metadata/",file_path)
        if not os.path.exists(path):
            os.mkdir(path)

        # Saving the information in the database
        # document_path_folder(path=file_path)
        document = Document(title=title, uploadedFile=uploadedFile, file_path=path)
        document.save()
        # documents = Document.objects.all()
        
        # read excel file xlrd example
        book = xlrd.open_workbook("documents/metadata/METADATA_LAB_RESPIRATORIOS_V2_WvwyN8Q.xlsx")
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
