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

def index(request):
    index_data = core.services.get_index_data()
    samples_count =  {item["state_id__state"]: item["count"] for item in index_data["number_of_samples"]}
    return render(
        request,
        "core/index.html",
        {
            "number_of_samples": samples_count,
            "nextstrain_url": index_data["nextstrain_url"],
        }
    )

@login_required
def assign_samples_to_user(request):
    if request.user.username != "admin":
        return redirect("/")

    # Load lab/user data to always include it
    if request.method == "POST" and request.POST.get("action") == "assignSamples":
        lab_data = core.services.assign_samples_to_user_by_lab(
            lab=request.POST.get("lab"),
            user_id=request.POST.get("userName")
        )
    else:
        lab_data = core.services.get_labs_and_users_data()
    return render(request, "core/assignSamplesToUser.html", {"lab_data": lab_data})


# TODO: this needs serialized-based refactor 
@login_required
def sample_display(request, sample_id):
    sample_data = core.utils.samples.get_sample_display_data(sample_id, request.user)
    if "ERROR" in sample_data:
        return render(
            request, "core/sampleDisplay.html", {"ERROR": sample_data["ERROR"]}
        )
    sample_data["gisaid"] = core.utils.public_db.get_public_information_from_sample(
        "gisaid", sample_id
    )
    sample_data["ena"] = core.utils.public_db.get_public_information_from_sample(
        "ena", sample_id
    )
    # TODO: Reduce search waiting time by optimizing DB queries
    # FIXME: Some tables in the template appear abnormally. Fix it and discuss the strategy followed in get_bioinfo_analysis_data_from_sample
    sample_data["bioinfo"] = (
        core.utils.bioinfo_analysis.get_bioinfo_analysis_data_from_sample(sample_id)
    )
    sample_data["lineage"] = core.utils.lineage.get_lineage_data_from_sample(sample_id)
    sample_data["variant"] = core.utils.variants.get_variant_data_from_sample(sample_id)
    # Display graphic only if variant data are for the sample
    if "heading" in sample_data["variant"]:
        sample_data["graphic"] = core.utils.variants.get_variant_graphic_from_sample(
            sample_id
        )
    return render(request, "core/sampleDisplay.html", {"sample_data": sample_data})

# TODO: this needs serialized-based refactor
@login_required
def schema_handling(request):
    if request.user.username != "admin":
        return redirect("/")
    if request.method == "POST" and request.POST["action"] == "uploadSchema":
        if "schemaDefault" in request.POST:
            schemaDefault = "on"
        else:
            schemaDefault = "off"
        schema_data = core.utils.schema.process_schema_file(
            request.FILES["schemaFile"],
            schemaDefault,
            request.user,
            __package__,
        )
        if "ERROR" in schema_data:
            return render(
                request,
                "core/schemaHandling.html",
                {"ERROR": schema_data["ERROR"]},
            )
        schemas = core.utils.schema.get_schemas_loaded(__package__)
        return render(
            request,
            "core/schemaHandling.html",
            {"SUCCESS": schema_data["SUCCESS"], "schemas": schemas},
        )
    schemas = core.utils.schema.get_schemas_loaded(__package__)
    return render(request, "core/schemaHandling.html", {"schemas": schemas})

# TODO: this needs serialized-based refactor
@login_required
def schema_display(request, schema_id):
    if request.user.username != "admin":
        return redirect("/")
    schema_data = core.utils.schema.get_schema_display_data(schema_id)
    return render(request, "core/schemaDisplay.html", {"schema_data": schema_data})


@login_required
def search_sample(request):
    """Search sample using the filter in the form"""
    search_data = core.services.get_search_data(user_obj=request.user)
    if request.method == "POST" and request.POST.get("action") == "searchSample":
        sample_name = request.POST.get("sampleName", "")
        s_date = request.POST.get("sDate", "")
        lab_name = request.POST.get("lab", "")
        sample_state = request.POST.get("sampleState", "")

        # check that some values are in the request if not return the form
        if not any([sample_name, s_date, lab_name, sample_state]):
            return render(
                request, "core/searchSample.html", {"search_data": search_data}
            )

        # check the right format of s_date
        if s_date != "" and not core.utils.generic_functions.check_valid_date_format(
            s_date
        ):
            return render(
                request,
                "core/searchSample.html",
                {
                    "search_data": search_data,
                    "warning": core.config.ERROR_INVALID_DEFINED_SAMPLE_FORMAT,
                },
            )

        # Generate sample display data
        display_data = core.services.display_samples(
            sample_name=sample_name,
            lab_name=lab_name,
            sample_state=sample_state,
            s_date=s_date,
            user=request.user
        )
        list_display = display_data["list_display"]
        # Redirection (samples == 1 )
        if list_display["redirect"]:
            return redirect(
                "sample_display", 
                sample_id=list_display["redirect"]
            )
        if list_display["ERROR"]:
            return render(
                request,
                "core/searchSample.html",
                {
                    "search_data": search_data,
                    "ERROR": list_display["ERROR"]
                }
            )
        # POST return sample list display
        return render(request,
            "core/searchSample.html",
            {"list_display": list_display}
        )

    # GET returns search data
    return render(
        request,
        "core/searchSample.html",
        {"search_data": search_data}
    )

# TODO: this needs serialized-based refactor
# FIXME: This needs a template or error message when user != admin tryies to access.
@login_required
def metadata_visualization(request):
    if request.user.username != "admin":
        return redirect("/")
    if request.method == "POST" and request.POST["action"] == "selectFields":
        selected_fields = core.utils.schema.store_fields_metadata_visualization(
            request.POST
        )
        if "ERROR" in selected_fields:
            m_visualization = core.utils.schema.get_fields_from_schema(
                core.utils.schema.get_schema_obj_from_id(request.POST["schemaID"])
            )
            return render(
                request,
                "core/metadataVisualization.html",
                {"ERROR": selected_fields, "m_visualization": m_visualization},
            )
        return render(
            request,
            "core/metadataVisualization.html",
            {"SUCCESS": selected_fields},
        )
    if request.method == "POST" and request.POST["action"] == "deleteFields":
        core.utils.schema.del_metadata_visualization()
        return render(request, "core/metadataVisualization.html", {"DELETE": "DELETE"})
    metadata_obj = core.utils.schema.get_latest_schema("Relecov", __package__)
    if isinstance(metadata_obj, dict):
        return render(
            request,
            "core/metadataVisualization.html",
            {"ERROR": metadata_obj["ERROR"]},
        )
    data_visualization = core.utils.schema.fetch_info_meta_visualization(metadata_obj)
    if isinstance(data_visualization, dict):
        return render(
            request,
            "core/metadataVisualization.html",
            {"data_visualization": data_visualization},
        )
    m_visualization = core.utils.schema.get_fields_from_schema(metadata_obj)
    return render(
        request,
        "core/metadataVisualization.html",
        {"m_visualization": m_visualization},
    )

# TODO: Testing required
@login_required
def intranet(request):
    is_manager = Group.objects.filter(name="RelecovManager").last() in request.user.groups.all()

    # Generate data for manager access
    if is_manager:
        manager_intra_data = core.services.get_intranet_data_for_manager()
        return render(request, "core/intranet.html", {"manager_intra_data": manager_intra_data})

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
