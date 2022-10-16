from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from relecov_core.utils.handling_samples import (
    analyze_input_samples,
    count_samples_in_all_tables,
    check_if_empty_data,
    create_form_for_batch,
    create_metadata_form,
    get_sample_display_data,
    get_search_data,
    join_sample_and_batch,
    pending_samples_in_metadata_form,
    save_temp_sample_data,
    search_samples,
    update_temporary_sample_table,
    write_form_data_to_excel,
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

from relecov_core.utils.handling_bioinfo_analysis import (
    get_bioinfo_analysis_data_from_sample,
)
from relecov_core.utils.handling_lab import (
    get_lab_contact_details,
    get_submitted_history_data,
    update_contact_lab,
)

from relecov_core.utils.handling_variant import get_variant_data_from_sample
from relecov_core.utils.bio_info_json_handling import process_bioinfo_file
from relecov_core.utils.generic_functions import check_valid_date_format
from relecov_core.utils.handling_annotation import (
    read_gff_file,
    stored_gff,
    get_annotations,
    check_if_annotation_exists,
    get_annotation_data,
)
from relecov_core.utils.handling_lineage import get_lineage_data_from_sample

from relecov_core.core_config import (
    ERROR_USER_FIELD_DOES_NOT_ENOUGH_CHARACTERS,
    ERROR_USER_IS_NOT_ASSIGNED_TO_LAB,
    ERROR_INVALID_DEFINED_SAMPLE_FORMAT,
    ERROR_NOT_MATCHED_ITEMS_IN_SEARCH,
    HEADING_FOR_SAMPLE_LIST,
)


def index(request):
    number_of_samples = count_samples_in_all_tables()

    return render(
        request,
        "relecov_core/index.html",
        {"number_of_samples": number_of_samples},
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
    # test flake working fine
    return render(request, "relecov_core/bioInfoJSONHandling.html", {})


@login_required
def sample_display(request, sample_id):
    sample_data = get_sample_display_data(sample_id, request.user)
    if "ERROR" in sample_data:
        return render(
            request, "relecov_core/sampleDisplay.html", {"ERROR": sample_data["ERROR"]}
        )
    sample_data["bioinfo"] = get_bioinfo_analysis_data_from_sample(sample_id)
    sample_data["lineage"] = get_lineage_data_from_sample(sample_id)
    sample_data["variant"] = get_variant_data_from_sample(sample_id)
    return render(
        request, "relecov_core/sampleDisplay.html", {"sample_data": sample_data}
    )


@login_required
def schema_handling(request):
    if request.user.username != "admin":
        return redirect("/")
    if request.method == "POST" and request.POST["action"] == "uploadSchema":
        if "schemaDefault" in request.POST:
            schemaDefault = "on"
        else:
            schemaDefault = "off"
        schema_data = process_schema_file(
            request.FILES["schemaFile"],
            schemaDefault,
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
        sample_list = search_samples(
            sample_name, user_name, sample_state, s_date, request.user
        )
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
            return redirect("sample_display", sample_id=sample_list[0])
        else:
            sample = {"s_data": sample_list, "heading": HEADING_FOR_SAMPLE_LIST}
            return render(
                request, "relecov_core/searchSample.html", {"list_display": sample}
            )
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
    lab_all_submits = get_submitted_history_data(request.user)

    if "ERROR" in lab_all_submits:
        return render(
            request, "relecov_core/intranet.html", {"ERROR": lab_all_submits["ERROR"]}
        )
    return render(request, "relecov_core/intranet.html", {"data": lab_all_submits})


def variants(request):
    return render(request, "relecov_core/variants.html", {})


@login_required()
def metadata_form(request):
    schema_obj = get_latest_schema("relecov", __package__)
    if request.method == "POST" and request.POST["action"] == "defineSamples":
        res_analyze = analyze_input_samples(request)
        # empty form
        if len(res_analyze) == 0:
            m_form = create_metadata_form(schema_obj, request.user)
            return render(request, "relecov_core/metadataForm.html", {"m_form": m_form})
        if "save_samples" in res_analyze:
            s_saved = save_temp_sample_data(res_analyze["save_samples"], request.user)
        if "s_incomplete" in res_analyze:
            return render(
                request,
                "relecov_core/metadataForm.html",
                {"s_incomplete": res_analyze["s_incomplete"], "m_form": m_form},
            )
        m_batch_form = create_form_for_batch(schema_obj, request.user)
        return render(
            request,
            "relecov_core/metadataForm.html",
            {"m_batch_form": m_batch_form, "sample_saved": s_saved},
        )
    if request.method == "POST" and request.POST["action"] == "defineBatch":
        if not check_if_empty_data(request.POST):
            m_batch_form = create_form_for_batch(schema_obj, request.user)
            return render(
                request,
                "relecov_core/metadataForm.html",
                {"m_batch_form": m_batch_form},
            )
        meta_data = join_sample_and_batch(request.POST, request.user, schema_obj)
        # write date to excel using relecov tools
        write_form_data_to_excel(meta_data, request.user)
        update_temporary_sample_table(request.user)
        # Display page to indicate that process is starting
        return render(
            request, "relecov_core/metadataForm.html", {"sample_recorded": "ok"}
        )
    else:
        if pending_samples_in_metadata_form(request.user):
            m_batch_form = create_form_for_batch(schema_obj, request.user)

            return render(
                request,
                "relecov_core/metadataForm.html",
                {"m_batch_form": m_batch_form},
            )
        m_form = create_metadata_form(schema_obj, request.user)
        if "ERROR" in m_form:
            return render(
                request, "relecov_core/metadataForm.html", {"ERROR": m_form["ERROR"]}
            )
        if m_form["lab_name"] == "":
            return render(
                request,
                "relecov_core/metadataForm.html",
                {"ERROR": ERROR_USER_IS_NOT_ASSIGNED_TO_LAB},
            )
        return render(request, "relecov_core/metadataForm.html", {"m_form": m_form})


@login_required()
def annotation_display(request, annot_id):
    """Display the full information about the organism annotation stored in
    database
    """
    if request.user.username != "admin":
        return redirect("/")
    if not check_if_annotation_exists(annot_id):
        return render(request, "relecov_core/error_404.html")
    annot_data = get_annotation_data(annot_id)
    return render(
        request, "relecov_core/annotationDisplay.html", {"annotation_data": annot_data}
    )


@login_required()
def virus_annotation(request):
    """Store the organism annotation gff file"""
    if request.user.username != "admin":
        return redirect("/")
    annotations = get_annotations()
    if request.method == "POST" and request.POST["action"] == "uploadAnnotation":
        gff_parsed = read_gff_file(request.FILES["gffFile"])
        if "ERROR" in gff_parsed:
            return render(
                request,
                "relecov_core/virusAnnotation.html",
                {"ERROR": gff_parsed["ERROR"], "annotations": annotations},
            )
        stored_gff(gff_parsed, request.user)
        annotations = get_annotations()
        return render(
            request,
            "relecov_core/virusAnnotation.html",
            {"SUCCESS": "Success", "annotations": annotations},
        )
    return render(
        request, "relecov_core/virusAnnotation.html", {"annotations": annotations}
    )


@login_required()
def laboratory_contact(request):
    lab_data = get_lab_contact_details(request.user)
    if "ERROR" in lab_data:
        return render(
            request, "relecov_core/laboratoryContact.html", {"ERROR": lab_data["ERROR"]}
        )
    if request.method == "POST" and request.POST["action"] == "updateLabData":
        result = update_contact_lab(lab_data, request.POST)
        if isinstance(result, dict):
            return render(
                request,
                "relecov_core/laboratoryContact.html",
                {"ERROR": result["ERROR"]},
            )
        return render(
            request, "relecov_core/laboratoryContact.html", {"Success": "Success"}
        )
    return render(
        request, "relecov_core/laboratoryContact.html", {"lab_data": lab_data}
    )


def contact(request):
    return render(request, "relecov_core/contact.html", {})
