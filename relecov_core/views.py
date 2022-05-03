from distutils.log import debug
from multiprocessing import context, Manager
from relecov_core.models import *
from django.shortcuts import render
from relecov_core.utils.feed_db import *
from relecov_core.utils.form.handling_samples import (
    get_input_samples,
    analyze_input_samples,
)
from relecov_core.utils.random_data import generate_random_sequences, generate_weeks
from relecov_core.utils.parse_files import *

# IMPORT FROM UTILS
from relecov_core.utils import *

# plotly dash
import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from django.contrib.auth.decorators import login_required


def index(request):
    context = {}
    return render(request, "relecov_core/index.html", context)


@login_required
def intranet(request):
    # return render(request, "relecov_core/relecovForm.html")
    return render(request, "relecov_core/intranet2.html")


def variants(request):
    context = {}
    return render(request, "relecov_core/variants.html", context)


def documentation(request):
    context = {}
    return render(request, "relecov_core/documentation.html", context)


@login_required()
def metadata_form(request):
    sample_recorded = get_input_samples(request)
    if request.method == "POST" and request.POST["action"] == "sampledefinition":
        sample_recorded = analyze_input_samples(request)
        # import pdb; pdb.set_trace()
    return render(
        request, "relecov_core/metadataForm.html", {"sample_recorded": sample_recorded}
    )


@login_required()
def contributor_info(request):
    if request.method == "POST":  # and request.POST['action'] == 'sampledefinition':
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


"""
def intranet2(request):

    return render(request, "relecov_core/intranet2.html", {})
"""
