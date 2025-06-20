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


# Imports for received samples graphic at intranet
import core.utils.samples_graphics
import core.utils.samples_map


# FIXME: This needs to homogenize the way passing data to template.
# FIXME: fornt end needs to manage error screen
# TODO: update the strucuture object that its going to be rendered
def index(request):
    index_data = core.services.get_index_data()
    return render(request, "core/index.html", {"data": index_data["data"]})


@login_required
def assign_samples_to_user(request):
    if request.user.username != "admin":
        return redirect("/")

    action = request.POST.get("action") if request.POST else None
    lab = request.POST.get("lab")
    user_id = request.POST.get("userName")

    response = core.services.get_assign_samples_data(
        action=action, lab=lab, user_id=user_id
    )
    return render(
        request,
        "core/assignSamplesToUser.html",
        {
            "data": response["data"],
            "success": response["success"] if action else None,
            "errors": response["errors"],
        },
    )


# TODO: Discuss whether render shuld be used once or twice (one if not result["success"] and another one if result["success"]). Example below shows an scenario where render is used once, letting the logic of errors to be addressed in the tempalte.
# TODO: I think it would be better to put here the request POST/GET logic.
@login_required
def schema_handling(request):
    if request.user.username != "admin":
        return redirect("/")
    result = core.services.get_schema_handling_data(request)
    show_success = request.method == "POST" and result.get("success")
    return render(
        request,
        "core/schemaHandling.html",
        {
            "DATA": result["data"],
            "SUCCESS": result["success"] if show_success else None,
            "ERROR": result["errors"],
        },
    )


@login_required
def schema_display(request, schema_id):
    if request.user.username != "admin":
        return redirect("/")
    schema_data = core.utils.schema.get_schema_display_data(schema_id)
    return render(request, "core/schemaDisplay.html", {"schema_data": schema_data})


@login_required
def sample_display(request, sample_id):
    result = core.services.get_sample_display_data(sample_id, request.user)
    if not result["success"]:
        return render(request, "core/sampleDisplay.html", {"errors": result["errors"]})

    return render(request, "core/sampleDisplay.html", {"data": result["data"]})


@login_required
def search_sample(request):
    """Search sample using the filter in the form"""
    search_data = core.services.get_search_data(user_obj=request.user)
    if request.method == "POST" and request.POST.get("action") == "searchSample":
        sample_name = request.POST.get("sampleName", "")
        s_date = request.POST.get("sDate", "")
        lab_name = request.POST.get("lab", "")
        sample_state = request.POST.get("sampleState", "")

        # Validate search parameters
        validation = core.services.validate_search_params(
            sample_name, lab_name, sample_state, s_date
        )
        if "warning" in validation:
            return render(
                request,
                "core/searchSample.html",
                {"DATA_QUERY": search_data, "ERROR": validation["warning"]},
            )

        # Get the search results
        display_result = core.services.display_samples(
            sample_name=sample_name,
            lab_name=lab_name,
            sample_state=sample_state,
            s_date=s_date,
            user=request.user,
        )
        display_data = display_result["data"]

        # If only one sample is found, redirect to sample display page
        if display_data.get("redirect"):
            return redirect("sample_display", sample_id=display_data["redirect"])

        # If more than one sample is found, render the list of records
        if (
            display_result["success"]
            and display_data.get("samples")
            and len(display_data["samples"]) > 1
        ):
            return render(
                request,
                "core/searchSample.html",
                {
                    "DATA_QUERY": display_data,
                    "SUCCESS": display_result["success"],
                    "ERROR": display_result["errors"],
                },
            )

        # If there are errors, render the error message
        if display_result["errors"]:
            return render(
                request,
                "core/searchSample.html",
                {"DATA_QUERY": search_data, "ERROR": display_result["errors"]},
            )

        # If no results but no explicit error, render the search form again
        return render(request, "core/searchSample.html", {"DATA_QUERY": search_data})

    # GET request or first access
    if "ERROR" in search_data:
        return render(
            request, "core/searchSample.html", {"ERROR": search_data["ERROR"]}
        )
    return render(request, "core/searchSample.html", {"DATA_DISPLAY": search_data})


@login_required
def metadata_visualization(request):
    if request.user.username != "admin":
        return redirect("/")
    result = core.services.handle_metadata_visualization(request)
    return render(
        request,
        "core/metadataVisualization.html",
        {
            "DATA": result["data"],
            "SUCCESS": result["success"],
            "ERROR": result["errors"],
        },
    )


@login_required
def intranet(request):
    is_manager = (
        Group.objects.filter(name="RelecovManager").last() in request.user.groups.all()
    )

    # Generate data for manager access
    if is_manager:
        manager_intra_data = core.services.get_intranet_data_for_manager()
        return render(
            request, "core/intranet.html", {"manager_intra_data": manager_intra_data}
        )

    # TODO: Didn't tested due to lack of bioinfodata (api related issues)
    intra_data = core.services.get_intranet_data_for_user(request.user)
    return render(request, "core/intranet.html", {"intra_data": intra_data})


def variants(request):
    return render(request, "core/variants.html", {})


# TODO: this needs serialized-based refactor
@login_required()
def metadata_form(request):
    schema_obj = core.utils.schema.get_latest_schema("relecov", __package__)
    if request.method == "POST" and request.POST["action"] == "uploadMetadataFile":
        if "metadataFile" in request.FILES:
            core.utils.samples.save_excel_form_in_samba_folder(
                request.FILES["metadataFile"], request.user.username
            )
            return render(
                request,
                "core/metadataForm.html",
                {"sample_recorded": {"ok": "OK"}},
            )
    if request.method == "POST" and request.POST["action"] == "defineSamples":
        res_analyze = core.utils.samples.analyze_input_samples(request)
        # empty form
        if len(res_analyze) == 0:
            m_form = core.utils.samples.create_metadata_form(schema_obj, request.user)
            return render(request, "core/metadataForm.html", {"m_form": m_form})
        if "save_samples" in res_analyze:
            s_saved = core.utils.samples.save_temp_sample_data(
                res_analyze["save_samples"], request.user
            )
        if "s_incomplete" in res_analyze or "s_already_record" in res_analyze:
            if "s_incomplete" not in res_analyze:
                m_form = None
            else:
                m_form = core.utils.samples.create_metadata_form(
                    schema_obj, request.user
                )
            return render(
                request,
                "core/metadataForm.html",
                {"sample_issues": res_analyze, "m_form": m_form},
            )
        m_batch_form = core.utils.samples.create_form_for_batch(
            schema_obj, request.user
        )
        sample_saved = core.utils.samples.get_sample_pre_recorded(request.user)
        return render(
            request,
            "core/metadataForm.html",
            {"m_batch_form": m_batch_form, "sample_saved": s_saved},
        )
    if request.method == "POST" and request.POST["action"] == "defineBatch":
        if not core.utils.samples.check_if_empty_data(request.POST):
            sample_saved = core.utils.samples.get_sample_pre_recorded(request.user)
            m_batch_form = core.utils.samples.create_form_for_batch(
                schema_obj, request.user
            )
            return render(
                request,
                "core/metadataForm.html",
                {"m_batch_form": m_batch_form, "sample_saved": sample_saved},
            )
        meta_data = core.utils.samples.join_sample_and_batch(
            request.POST, request.user, schema_obj
        )
        # write date to excel using relecov tools
        core.utils.samples.write_form_data_to_excel(meta_data, request.user)
        core.utils.samples.delete_temporary_sample_table(request.user)
        # Display page to indicate that process is starting
        return render(
            request, "core/metadataForm.html", {"sample_recorded": {"ok": "OK"}}
        )
    else:
        if core.utils.samples.pending_samples_in_metadata_form(request.user):
            sample_saved = core.utils.samples.get_sample_pre_recorded(request.user)
            m_batch_form = core.utils.samples.create_form_for_batch(
                schema_obj, request.user
            )
            return render(
                request,
                "core/metadataForm.html",
                {"m_batch_form": m_batch_form, "sample_saved": sample_saved},
            )
        m_form = core.utils.samples.create_metadata_form(schema_obj, request.user)
        if "ERROR" in m_form:
            return render(request, "core/metadataForm.html", {"ERROR": m_form["ERROR"]})
        if m_form["lab_name"] == "":
            return render(
                request,
                "core/metadataForm.html",
                {"ERROR": core.config.ERROR_USER_IS_NOT_ASSIGNED_TO_LAB},
            )
        return render(request, "core/metadataForm.html", {"m_form": m_form})


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
        if "ERROR" in gff_parsed:
            return render(
                request,
                "core/organismAnnotation.html",
                {"ERROR": gff_parsed["ERROR"], "annotations": annotations},
            )
        core.utils.annotation.store_gff(gff_parsed, request.user)
        annotations = core.utils.annotation.get_annotations()
        return render(
            request,
            "core/organismAnnotation.html",
            {"SUCCESS": "Success", "annotations": annotations},
        )
    return render(request, "core/organismAnnotation.html", {"annotations": annotations})


# TODO: this needs serialized-based refactor
@login_required()
def laboratory_contact(request):
    lab_data = core.utils.labs.get_lab_contact_details(request.user)
    if "ERROR" in lab_data:
        return render(
            request, "core/laboratoryContact.html", {"ERROR": lab_data["ERROR"]}
        )
    if request.method == "POST" and request.POST["action"] == "updateLabData":
        result = core.utils.labs.update_contact_lab(lab_data, request.POST)
        if isinstance(result, dict):
            return render(
                request,
                "core/laboratoryContact.html",
                {"ERROR": result["ERROR"]},
            )
        return render(request, "core/laboratoryContact.html", {"Success": "Success"})
    return render(request, "core/laboratoryContact.html", {"lab_data": lab_data})


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
