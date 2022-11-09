from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

from relecov_core.utils.handling_samples import (
    analyze_input_samples,
    assign_samples_to_new_user,
    count_handled_samples,
    check_if_empty_data,
    create_dash_bar_for_each_lab,
    create_form_for_batch,
    create_metadata_form,
    create_percentage_gauge_graphic,
    create_date_sample_bar,
    get_lab_last_actions,
    get_sample_display_data,
    get_search_data,
    get_sample_per_date_per_all_lab,
    get_sample_per_date_per_lab,
    get_sample_pre_recorded,
    get_sample_objs_per_lab,
    join_sample_and_batch,
    pending_samples_in_metadata_form,
    save_temp_sample_data,
    save_excel_form_in_samba_folder,
    search_samples,
    delete_temporary_sample_table,
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
    get_bio_analysis_stats_from_lab,
)
from relecov_core.utils.handling_lab import (
    get_all_defined_labs,
    get_lab_contact_details,
    get_lab_name_from_user,
    update_contact_lab,
)
from relecov_core.utils.handling_public_database import (
    get_public_accession_from_sample_lab,
    get_public_information_from_sample,
    percentage_graphic,
)
from relecov_core.utils.handling_variant import (
    get_variant_data_from_sample,
    get_variant_graphic_from_sample,
)
from relecov_core.utils.bio_info_json_handling import process_bioinfo_file
from relecov_core.utils.generic_functions import (
    check_valid_date_format,
    get_defined_users,
)
from relecov_core.utils.handling_annotation import (
    read_gff_file,
    stored_gff,
    get_annotations,
    check_if_annotation_exists,
    get_annotation_data,
)
from relecov_core.utils.handling_lineage import get_lineage_data_from_sample

from relecov_core.core_config import (
    ERROR_USER_IS_NOT_ASSIGNED_TO_LAB,
    ERROR_INVALID_DEFINED_SAMPLE_FORMAT,
    ERROR_NOT_MATCHED_ITEMS_IN_SEARCH,
    HEADING_FOR_SAMPLE_LIST,
)


def index(request):
    number_of_samples = count_handled_samples()
    return render(
        request, "relecov_core/index.html", {"number_of_samples": number_of_samples}
    )


@login_required
def assign_samples_to_user(request):
    if request.user.username != "admin":
        return redirect("/")
    if request.method == "POST" and request.POST["action"] == "assignSamples":
        assign = assign_samples_to_new_user(request.POST)
        return render(request, "relecov_core/assignSamplesToUser.html", assign)

    lab_data = {}
    lab_data["labs"] = get_all_defined_labs()
    lab_data["users"] = get_defined_users()
    return render(
        request,
        "relecov_core/assignSamplesToUser.html",
        {"lab_data": lab_data},
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
    sample_data["gisaid"] = get_public_information_from_sample("gisaid", sample_id)
    sample_data["ena"] = get_public_information_from_sample("ena", sample_id)
    sample_data["bioinfo"] = get_bioinfo_analysis_data_from_sample(sample_id)
    sample_data["lineage"] = get_lineage_data_from_sample(sample_id)
    sample_data["variant"] = get_variant_data_from_sample(sample_id)
    # Display graphic only if variant data are for the sample
    if "heading" in sample_data["variant"]:
        sample_data["graphic"] = get_variant_graphic_from_sample(sample_id)
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
    search_data = get_search_data(request.user)
    if request.method == "POST" and request.POST["action"] == "searchSample":
        sample_name = request.POST["sampleName"]
        s_date = request.POST["sDate"]
        lab_name = request.POST["lab"]
        sample_state = request.POST["sampleState"]
        # check that some values are in the request if not return the form
        if lab_name == "" and s_date == "" and sample_name == "" and sample_state == "":
            return render(
                request, "relecov_core/searchSample.html", {"search_data": search_data}
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
            sample_name, lab_name, sample_state, s_date, request.user
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
    relecov_group = Group.objects.get(name="RelecovManager")
    if relecov_group not in request.user.groups.all():
        intra_data = {}
        lab_name = get_lab_name_from_user(request.user)
        date_lab_samples = get_sample_per_date_per_lab(lab_name)
        if len(date_lab_samples) > 0:
            sample_lab_objs = get_sample_objs_per_lab(lab_name)
            analysis_percent = get_bio_analysis_stats_from_lab(lab_name)
            cust_data = {
                "col_names": ["Sequencing Date", "Number of samples"],
                "options": {},
            }
            cust_data["options"]["title"] = "Samples Received"
            cust_data["options"]["width"] = 600
            intra_data["sample_bar_graph"] = create_date_sample_bar(
                date_lab_samples, cust_data
            )
            intra_data["sample_gauge_graph"] = create_percentage_gauge_graphic(
                analysis_percent
            )
            intra_data["actions"] = get_lab_last_actions(lab_name)
            gisaid_acc = get_public_accession_from_sample_lab(
                "gisaid_accession_id", sample_lab_objs
            )
            if len(gisaid_acc) > 0:
                intra_data["gisaid_accession"] = gisaid_acc
            intra_data["gisaid_graph"] = percentage_graphic(
                len(sample_lab_objs), len(gisaid_acc), ""
            )
            ena_acc = get_public_accession_from_sample_lab(
                "ena_sample_accession", sample_lab_objs
            )
            if len(ena_acc) > 0:
                intra_data["ena_accession"] = ena_acc
                intra_data["ena_graph"] = percentage_graphic(
                    len(sample_lab_objs), len(ena_acc), ""
                )
        return render(request, "relecov_core/intranet.html", {"intra_data": intra_data})
    else:
        # loged user belongs to Relecov Manager group
        manager_intra_data = {}
        all_sample_per_date = get_sample_per_date_per_all_lab()
        num_of_samples = count_handled_samples()
        if len(all_sample_per_date) > 0:
            cust_data = {
                "col_names": ["Sequencing Date", "Number of samples"],
                "options": {},
            }
            cust_data["options"]["title"] = "Samples Received for all laboratories"
            cust_data["options"]["width"] = 590
            manager_intra_data["sample_bar_graph"] = create_date_sample_bar(
                all_sample_per_date, cust_data
            )
            # graph for percentage analysis
            analysis_percent = get_bio_analysis_stats_from_lab()
            manager_intra_data["sample_gauge_graph"] = create_percentage_gauge_graphic(
                analysis_percent
            )
            # dash graph for samples per lab
            create_dash_bar_for_each_lab()
            # Get the latest action from each lab
            manager_intra_data["actions"] = get_lab_last_actions()
            # Collect GISAID information
            gisaid_acc = get_public_accession_from_sample_lab(
                "gisaid_accession_id", None
            )
            if len(gisaid_acc) > 0:
                manager_intra_data["gisaid_accession"] = gisaid_acc
                manager_intra_data["gisaid_graph"] = percentage_graphic(
                    num_of_samples["Defined"], len(gisaid_acc), ""
                )
            # Collect Ena information
            ena_acc = get_public_accession_from_sample_lab("ena_sample_accession", None)
            if len(ena_acc) > 0:
                manager_intra_data["ena_accession"] = ena_acc
                manager_intra_data["ena_graph"] = percentage_graphic(
                    num_of_samples["Defined"], len(ena_acc), ""
                )
        # import pdb; pdb.set_trace()
        return render(
            request,
            "relecov_core/intranet.html",
            {"manager_intra_data": manager_intra_data},
        )


def variants(request):
    return render(request, "relecov_core/variants.html", {})


@login_required()
def metadata_form(request):
    schema_obj = get_latest_schema("relecov", __package__)
    if request.method == "POST" and request.POST["action"] == "uploadMetadataFile":
        if "metadataFile" in request.FILES:

            save_excel_form_in_samba_folder(
                request.FILES["metadataFile"], request.user.username
            )
            return render(
                request, "relecov_core/metadataForm.html", {"sample_recorded": "ok"}
            )
    if request.method == "POST" and request.POST["action"] == "defineSamples":
        res_analyze = analyze_input_samples(request)
        # empty form
        if len(res_analyze) == 0:
            m_form = create_metadata_form(schema_obj, request.user)
            return render(request, "relecov_core/metadataForm.html", {"m_form": m_form})
        if "save_samples" in res_analyze:
            s_saved = save_temp_sample_data(res_analyze["save_samples"], request.user)
        if "s_incomplete" in res_analyze or "s_already_record" in res_analyze:
            if "s_incomplete" not in res_analyze:
                m_form = None
            else:
                m_form = create_metadata_form(schema_obj, request.user)
            return render(
                request,
                "relecov_core/metadataForm.html",
                {"sample_issues": res_analyze, "m_form": m_form},
            )
        m_batch_form = create_form_for_batch(schema_obj, request.user)
        sample_saved = get_sample_pre_recorded(request.user)
        return render(
            request,
            "relecov_core/metadataForm.html",
            {"m_batch_form": m_batch_form, "sample_saved": s_saved},
        )
    if request.method == "POST" and request.POST["action"] == "defineBatch":
        if not check_if_empty_data(request.POST):
            sample_saved = get_sample_pre_recorded(request.user)
            m_batch_form = create_form_for_batch(schema_obj, request.user)
            return render(
                request,
                "relecov_core/metadataForm.html",
                {"m_batch_form": m_batch_form, "sample_saved": sample_saved},
            )
        meta_data = join_sample_and_batch(request.POST, request.user, schema_obj)
        # write date to excel using relecov tools
        write_form_data_to_excel(meta_data, request.user)
        delete_temporary_sample_table(request.user)
        # Display page to indicate that process is starting
        return render(
            request, "relecov_core/metadataForm.html", {"sample_recorded": "ok"}
        )
    else:
        if pending_samples_in_metadata_form(request.user):
            sample_saved = get_sample_pre_recorded(request.user)
            m_batch_form = create_form_for_batch(schema_obj, request.user)
            return render(
                request,
                "relecov_core/metadataForm.html",
                {"m_batch_form": m_batch_form, "sample_saved": sample_saved},
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
def organism_annotation(request):
    """Store the organism annotation gff file"""
    if request.user.username != "admin":
        return redirect("/")
    annotations = get_annotations()
    if request.method == "POST" and request.POST["action"] == "uploadAnnotation":
        gff_parsed = read_gff_file(request.FILES["gffFile"])
        if "ERROR" in gff_parsed:
            return render(
                request,
                "relecov_core/organismAnnotation.html",
                {"ERROR": gff_parsed["ERROR"], "annotations": annotations},
            )
        stored_gff(gff_parsed, request.user)
        annotations = get_annotations()
        return render(
            request,
            "relecov_core/organismAnnotation.html",
            {"SUCCESS": "Success", "annotations": annotations},
        )
    return render(
        request, "relecov_core/organismAnnotation.html", {"annotations": annotations}
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
