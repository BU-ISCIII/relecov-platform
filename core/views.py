# Generic imports
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
import core.api.serializers

# Local imports
import core.utils.samples
import core.utils.schema
import core.utils.bioinfo_analysis
import core.utils.labs
import core.utils.public_db
import core.utils.variants
import core.utils.generic_functions
import core.utils.annotation
import core.utils.lineage
import core.config
import core.services
from core.services import schema_services
from core.services import sample_services
from core.services import intranet_services
from core.services import metadata_services
from core.services import lab_services
from core.services import assignment_services


# Imports for received samples graphic at intranet
import core.utils.samples_graphics
import core.utils.samples_map


# FIXME: This needs to homogenize the way passing data to template.
# FIXME: fornt end needs to manage error screen
# TODO: update the strucuture object that its going to be rendered
def index(request):
    index_data = core.services.get_index_data()
    return render(request, "core/index.html", {"data": index_data["data"]})


@login_required()
def assign_samples_to_user(request):
    if request.user.username != "admin":
        return redirect("/")

    action = request.POST.get("action") if request.method == "POST" else None
    response = assignment_services.handle_assign_samples_to_user(
        action=action,
        post_data=request.POST if request.method == "POST" else None,
        user=request.user,
    )
    context = {
        **response.get("data", {}),
        "success": response.get("success"),
        "errors": response.get("errors"),
    }
    return render(request, "core/assignSamplesToUser.html", context)


# TODO: Discuss whether render shuld be used once or twice (one if not result["success"] and another one if result["success"]). Example below shows an scenario where render is used once, letting the logic of errors to be addressed in the tempalte.
# TODO: I think it would be better to put here the request POST/GET logic.
@login_required
def schema_handling(request):
    if request.user.username != "admin":
        return redirect("/")

    action = request.POST.get("action") if request.method == "POST" else None
    schema_file = request.FILES.get("schemaFile") if request.method == "POST" else None
    default_flag = "on" if request.POST.get("schemaDefault") else "off"

    response = schema_services.handle_schema_upload(
        action=action,
        schema_file=schema_file,
        default_flag=default_flag,
        user=request.user,
        app_name=__package__,
    )

    context = {**response.get("data", {}), "success": response.get("success"), "errors": response.get("errors")}
    return render(request, "core/schemaHandling.html", context)


@login_required
def schema_display(request, schema_id):
    if request.user.username != "admin":
        return redirect("/")
    response = schema_services.get_schema_display(schema_id)
    context = {
        **response.get("data", {}),
        "success": response.get("success"),
        "errors": response.get("errors"),
    }
    return render(request, "core/schemaDisplay.html", context)


@login_required
def sample_display(request, sample_id):
    response = core.services.get_sample_display_data(sample_id, request.user)
    context = {
        **response.get("data", {}),
        "success": response.get("success"),
        "errors": response.get("errors"),
    }
    return render(request, "core/sampleDisplay.html", context)


@login_required
def search_sample(request):
    """Search sample using the filter in the form"""
    action = request.POST.get("action") if request.method == "POST" else None
    sample_name = request.POST.get("sampleName", "")
    s_date = request.POST.get("sDate", "")
    lab_name = request.POST.get("lab", "")
    sample_state = request.POST.get("sampleState", "")

    response = sample_services.handle_sample_search(
        action=action,
        sample_name=sample_name,
        s_date=s_date,
        lab_name=lab_name,
        sample_state=sample_state,
        user=request.user,
    )

    redirect_id = response.get("data", {}).get("redirect")
    if redirect_id:
        return redirect("sample_display", sample_id=redirect_id)

    context = {
        **response.get("data", {}),
        "success": response.get("success"),
        "errors": response.get("errors"),
    }
    return render(request, "core/searchSample.html", context)


@login_required
def metadata_visualization(request):
    if request.user.username != "admin":
        return redirect("/")
    response = core.services.handle_metadata_visualization(request)
    context = {
        **(response.get("data") or {}),
        "success": response.get("success"),
        "errors": response.get("errors"),
    }
    return render(request, "core/metadataVisualization.html", context)


@login_required
def intranet(request):
    is_manager = (
        Group.objects.filter(name="RelecovManager").last() in request.user.groups.all()
    )

    if is_manager:
        response = intranet_services.get_intranet_data_for_manager()
        return render(
            request,
            "core/intranet.html",
            {
                "data": response["data"],
                "success": response["success"],
                "errors": response["errors"],
            },
        )

    # TODO: Didn't tested due to lack of bioinfodata (api related issues)
    response = intranet_services.get_intranet_data_for_user(request.user)
    return render(
        request,
        "core/intranet.html",
        {
            "data": response["data"],
            "success": response["success"],
            "errors": response["errors"],
        },
    )


def variants(request):
    return render(request, "core/variants.html", {})

# TODO: too many utils to apply serializer refactor
@login_required()
def metadata_form(request):
    schema_obj = core.utils.schema.get_latest_schema("relecov", __package__)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "uploadMetadataFile" and "metadataFile" in request.FILES:
            response = metadata_services.handle_metadata_upload(
                request.FILES["metadataFile"], request.user.username
            )
            return render(
                request, "core/metadataForm.html",
                {
                    "DATA_SAMPLERECORDED": response["data"].get("sample_recorded"),
                    "success": response["success"],
                    "errors": response["errors"]
                }
            )
        #TODO: fix in progress
        if action == "defineSamples":
            response = metadata_services.handle_define_samples(
                request.POST, request.user, schema_obj
            )
            if "sample_issues" in response["data"]:
                return render(
                    request, "core/metadataForm.html",
                    {
                        "DATA_SAMPLEISSUES": response["data"]["sample_issues"],
                        "DATA_FORM": response["data"]["m_form"],
                        "success": response["success"],
                        "errors": response["errors"]
                    }
                )
            if "m_form" in response["data"]:
                return render(
                    request, "core/metadataForm.html",
                    {
                        "DATA_FORM": response["data"]["m_form"],
                        "success": response["success"],
                        "errors": response["errors"]
                    }
                )
            if "m_batch_form" in response["data"]:
                return render(
                    request, "core/metadataForm.html",
                    {
                        "DATA_BATCHFORM": response["data"]["m_batch_form"],
                        "DATA_SAMPLESAVED": response["data"]["sample_saved"],
                        "success": response["success"],
                        "errors": response["errors"]
                    }
                )
            if "sample_saved" in response["data"]:
                return render(
                    request, "core/metadataForm.html",
                    {
                        "DATA_SAMPLESAVED": response["data"]["sample_saved"],
                        "success": response["success"],
                        "errors": response["errors"]
                    }
                )

        if action == "defineBatch":
            response = metadata_services.handle_define_batch(
                request.POST, request.user, schema_obj
            )
            if "m_batch_form" in response["data"]:
                return render(
                    request, "core/metadataForm.html",
                    {
                        "DATA_BATCHFORM": response["data"]["m_batch_form"],
                        "DATA_SAMPLESAVED": response["data"]["sample_saved"],
                        "success": response["success"],
                        "errors": response["errors"]
                    }
                )
            if "sample_recorded" in response["data"]:
                return render(
                    request, "core/metadataForm.html",
                    {
                        "DATA_SAMPLERECORDED": response["data"]["sample_recorded"],
                        "success": response["success"],
                        "errors": response["errors"]
                    }
                )

    # GET request or fallback
    response = metadata_services.get_metadata_form_initial(request.user, schema_obj)
    if "m_batch_form" in response["data"]:
        return render(
            request, "core/metadataForm.html",
            {
                "DATA_BATCHFORM": response["data"]["m_batch_form"],
                "DATA_SAMPLESAVED": response["data"]["sample_saved"],
                "success": response["success"],
                "errors": response["errors"]
            }
        )
    if not response["success"]:
        return render(
            request, "core/metadataForm.html",
            {"errors": response["errors"]}
        )
    return render(
        request, "core/metadataForm.html",
        {
            "DATA_FORM": response["data"]["m_form"],
            "success": response["success"],
            "errors": response["errors"]
        }
    )


# TODO: this needs serialized-based refactor
@login_required()
def annotation_display(request, annot_id):
    """Display the full information about the organism annotation stored in
    database
    """
    if request.user.username != "admin":
        return redirect("/")
    if not core.utils.annotation.check_if_annotation_exists(annot_id):
        return render(request, "core/error_404.html")
    annot_data = core.utils.annotation.get_annotation_data(annot_id)
    return render(
        request, "core/annotationDisplay.html", {"annotation_data": annot_data}
    )


# TODO: this needs serialized-based refactor
@login_required()
def organism_annotation(request):
    """Store the organism annotation gff file"""
    if request.user.username != "admin":
        return redirect("/")
    annotations = core.utils.annotation.get_annotations()
    if request.method == "POST" and request.POST["action"] == "uploadAnnotation":
        gff_parsed = core.utils.annotation.read_gff_file(request.FILES["gffFile"])
        if "errors" in gff_parsed:
            return render(
                request,
                "core/organismAnnotation.html",
                {"errors": gff_parsed["errors"], "annotations": annotations},
            )
        core.utils.annotation.store_gff(gff_parsed, request.user)
        annotations = core.utils.annotation.get_annotations()
        return render(
            request,
            "core/organismAnnotation.html",
            {"success": "Success", "annotations": annotations},
        )
    return render(request, "core/organismAnnotation.html", {"annotations": annotations})


# TODO: this needs serialized-based refactor
@login_required()
def laboratory_contact(request):
    action = request.POST.get("action") if request.method == "POST" else None
    response = lab_services.handle_laboratory_contact(
        action=action,
        post_data=request.POST if request.method == "POST" else None,
        user=request.user,
    )
    context = {
        **response.get("data", {}),
        "success": response.get("success"),
        "errors": response.get("errors"),
    }
    return render(request, "core/laboratoryContact.html", context)


# TODO: this needs serialized-based refactor
@login_required
def received_samples(request):
    sample_data = {}
    # samples receive over time map
    sample_data["map"] = core.utils.samples_map.create_samples_received_map()
    # samples receive over time graph
    # df = create_dataframe_from_json()
    # create_samples_over_time_graph(df)

    # # collecting now data from database
    sample_data["received_samples_graph"] = (
        core.utils.samples_graphics.received_samples_graph()
    )
    # Pie charts
    # data = parse_json_file()
    # create_samples_received_over_time_per_ccaa_pieChart(data)
    sample_data["samples_per_ccaa"] = core.utils.samples_graphics.received_per_ccaa()
    # create_samples_received_over_time_per_laboratory_pieChart(data)
    sample_data["samples_per_lab"] = core.utils.samples_graphics.received_per_lab()
    return render(
        request,
        "core/receivedSamples.html",
        {"sample_data": sample_data},
    )


def contact(request):
    return render(request, "core/contact.html", {})
