# Generic imports
from datetime import datetime
import csv
from io import BytesIO
import json
from collections import defaultdict, OrderedDict
import re
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from openpyxl import Workbook

# Local imports
import core.models
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

# Imports for received samples graphic at intranet
import core.utils.samples_graphics
import core.utils.samples_map

#  End of imports  received samples
import time

SEARCH_SAMPLE_COLUMNS = {
    0: "sequencing_id",
    1: "collection_date",
    2: "lineage",
    3: "collecting_institution",
}


def _get_search_sample_rows_for_user(user_obj):
    """Return search rows or an error payload for the given user."""
    if core.models.Sample.objects.count() == 0:
        return {"ERROR": core.config.ERROR_NOT_SAMPLES_HAVE_BEEN_DEFINED}

    all_samples_summary = core.utils.samples.get_search_table_for_user(user_obj)
    if isinstance(all_samples_summary, dict) and "ERROR" in all_samples_summary:
        return all_samples_summary

    if not all_samples_summary:
        user_lab = core.utils.labs.get_lab_name_from_user(user_obj)
        if not user_lab:
            return {"ERROR": "You don't have a laboratory assigned to you yet"}
        return {"ERROR": f"No samples found for your designated laboratory: {user_lab}"}

    return [
        {
            "id": sample_pk,
            "sequencing_id": sequencing_id,
            "collection_date": collection_date,
            "lineage": lineage,
            "collecting_institution": collecting_institution,
        }
        for sample_pk, sequencing_id, collection_date, lineage, collecting_institution in all_samples_summary
    ]


def _normalize_datatable_search_value(
    value, regex=False, json_list=False, json_object=False
):
    """Normalize DataTables search values, including escaped exact-match regexes."""
    if not value:
        return ""
    if json_list and value.startswith("[") and value.endswith("]"):
        try:
            return [
                str(item).strip() for item in json.loads(value) if str(item).strip()
            ]
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    if json_object and value.startswith("{") and value.endswith("}"):
        try:
            return {
                key: str(item).strip()
                for key, item in json.loads(value).items()
                if str(item).strip()
            }
        except (AttributeError, TypeError, ValueError, json.JSONDecodeError):
            pass
    if regex and value.startswith("^") and value.endswith("$"):
        value = value[1:-1]
        # DataTables' escapeRegex() prefixes regex metacharacters with a
        # backslash. The server performs a literal exact match, so restore the
        # original option value before comparing it with the sample data.
        value = re.sub(r"\\([.*+?^${}()|[\]\\/-])", r"\1", value)
    return value.strip()


def _row_matches_search(row, global_search, column_filters):
    """Return True if the row matches the global and column-specific filters."""
    if global_search:
        normalized_global = global_search.lower()
        if not any(
            normalized_global in str(row[field]).lower()
            for field in SEARCH_SAMPLE_COLUMNS.values()
        ):
            return False

    for field_name, search_value, exact_match in column_filters:
        if not search_value:
            continue
        candidate = str(row[field_name] or "")
        if isinstance(search_value, list):
            if candidate not in search_value:
                return False
            continue
        if isinstance(search_value, dict):
            start_date = search_value.get("from")
            end_date = search_value.get("to")
            if not candidate:
                return False
            if start_date and candidate < start_date:
                return False
            if end_date and candidate > end_date:
                return False
            continue
        if exact_match:
            if candidate != search_value:
                return False
        elif search_value.lower() not in candidate.lower():
            return False

    return True


def _get_sort_value(row, field_name):
    """Get a stable sort key for search sample rows."""
    value = row.get(field_name)
    if value is None:
        return ""
    if isinstance(value, str):
        return value.lower()
    return value


def index(request):
    number_of_samples = core.utils.samples.count_handled_samples()
    nextstrain_url = core.utils.generic_functions.get_configuration_value(
        "NEXTSTRAIN_URL"
    )
    return render(
        request,
        "core/index.html",
        {"number_of_samples": number_of_samples, "nextstrain_url": nextstrain_url},
    )


def cookie_policy(request):
    return render(request, "core/cookiePolicy.html")


def _get_cookie_consent_redirect(request):
    next_url = request.POST.get("next") or "/"
    if url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return "/"


@require_POST
def cookie_consent(request):
    consent_value = request.POST.get("value")
    if consent_value not in core.config.COOKIE_CONSENT_VALUES:
        return JsonResponse({"ok": False, "error": "Invalid consent value"}, status=400)

    response = redirect(_get_cookie_consent_redirect(request))
    response.set_cookie(
        core.config.COOKIE_CONSENT_NAME,
        f"{consent_value}|{timezone.now().isoformat()}",
        max_age=core.config.COOKIE_CONSENT_MAX_AGE,
        path="/",
        samesite="Lax",
        secure=request.is_secure(),
    )
    return response


@login_required
def assign_samples_to_user(request):
    if request.user.username != "admin":
        return redirect("/")
    if request.method == "POST" and request.POST["action"] == "assignSamples":
        assign = core.utils.samples.assign_samples_to_new_user(request.POST)
        return render(request, "core/assignSamplesToUser.html", assign)

    lab_data = {}
    lab_data["labs"] = core.utils.labs.get_all_defined_labs()
    lab_data["users"] = core.utils.generic_functions.get_defined_users()
    return render(
        request,
        "core/assignSamplesToUser.html",
        {"lab_data": lab_data},
    )


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


@login_required
def schema_display(request, schema_id):
    if request.user.username != "admin":
        return redirect("/")
    schema_data = core.utils.schema.get_schema_display_data(schema_id)
    return render(request, "core/schemaDisplay.html", {"schema_data": schema_data})


@login_required
def search_sample(request):
    """Search sample using the filter in the form"""
    sample_rows = _get_search_sample_rows_for_user(request.user)
    if isinstance(sample_rows, dict) and "ERROR" in sample_rows:
        return render(
            request,
            "core/searchSample.html",
            {
                "ERROR": sample_rows["ERROR"],
                "lineage_options": [],
                "collecting_institution_options": [],
            },
        )

    lineage_options = sorted({row["lineage"] for row in sample_rows if row["lineage"]})
    collecting_institution_options = sorted(
        {
            row["collecting_institution"]
            for row in sample_rows
            if row["collecting_institution"]
        }
    )
    return render(
        request,
        "core/searchSample.html",
        {
            "lineage_options": lineage_options,
            "collecting_institution_options": collecting_institution_options,
        },
    )


def _get_filtered_search_sample_data(request, sample_rows):
    """Apply DataTables search and ordering parameters to sample browser rows."""
    global_search = _normalize_datatable_search_value(
        request.GET.get("search[value]", ""),
        request.GET.get("search[regex]", "false").lower() == "true",
    ).lower()

    column_filters = []
    for index, field_name in SEARCH_SAMPLE_COLUMNS.items():
        search_value = _normalize_datatable_search_value(
            request.GET.get(f"columns[{index}][search][value]", ""),
            request.GET.get(f"columns[{index}][search][regex]", "false").lower()
            == "true",
            index == 3,
            index == 1,
        )
        exact_match = index in (2, 3)
        column_filters.append((field_name, search_value, exact_match))

    filtered_rows = [
        row
        for row in sample_rows
        if _row_matches_search(row, global_search, column_filters)
    ]

    lineage_option_filters = [
        column_filter
        for column_filter in column_filters
        if column_filter[0] != "lineage"
    ]
    lineage_options = sorted(
        {
            row["lineage"]
            for row in sample_rows
            if row["lineage"]
            and _row_matches_search(row, global_search, lineage_option_filters)
        }
    )

    institution_option_filters = [
        column_filter
        for column_filter in column_filters
        if column_filter[0] != "collecting_institution"
    ]
    collecting_institution_options = sorted(
        {
            row["collecting_institution"]
            for row in sample_rows
            if row["collecting_institution"]
            and _row_matches_search(row, global_search, institution_option_filters)
        }
    )

    order_column = request.GET.get("order[0][column]")
    order_direction = request.GET.get("order[0][dir]", "asc")
    if order_column is not None:
        try:
            order_column = int(order_column)
        except (TypeError, ValueError):
            order_column = None
    field_name = SEARCH_SAMPLE_COLUMNS.get(order_column, "sequencing_id")
    reverse_order = order_direction == "desc"
    filtered_rows.sort(
        key=lambda row: _get_sort_value(row, field_name), reverse=reverse_order
    )

    return filtered_rows, lineage_options, collecting_institution_options


@login_required
def search_sample_data(request):
    """Return paginated sample browser data for DataTables server-side mode."""
    sample_rows = _get_search_sample_rows_for_user(request.user)
    if isinstance(sample_rows, dict) and "ERROR" in sample_rows:
        try:
            draw = int(request.GET.get("draw", 0) or 0)
        except (TypeError, ValueError):
            draw = 0
        return JsonResponse(
            {
                "draw": draw,
                "recordsTotal": 0,
                "recordsFiltered": 0,
                "data": [],
                "error": sample_rows["ERROR"],
            }
        )

    try:
        draw = int(request.GET.get("draw", 0) or 0)
    except (TypeError, ValueError):
        draw = 0
    try:
        start = max(int(request.GET.get("start", 0) or 0), 0)
    except (TypeError, ValueError):
        start = 0
    try:
        length = int(request.GET.get("length", 25) or 25)
    except (TypeError, ValueError):
        length = 25

    (
        filtered_rows,
        lineage_options,
        collecting_institution_options,
    ) = _get_filtered_search_sample_data(request, sample_rows)

    if length == -1:
        paginated_rows = filtered_rows[start:]
    else:
        paginated_rows = filtered_rows[start : start + max(length, 0)]

    return JsonResponse(
        {
            "draw": draw,
            "recordsTotal": len(sample_rows),
            "recordsFiltered": len(filtered_rows),
            "data": paginated_rows,
            "lineage_options": lineage_options,
            "collecting_institution_options": collecting_institution_options,
        }
    )


@login_required
def search_sample_csv(request):
    """Download the currently filtered sample browser rows as CSV."""
    sample_rows = _get_search_sample_rows_for_user(request.user)
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="relecov_samples.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "Sample Sequencing ID",
            "Collection Date",
            "Lineage",
            "Collecting Institution",
        ]
    )

    if isinstance(sample_rows, dict) and "ERROR" in sample_rows:
        return response

    filtered_rows, _lineage_options, _institution_options = (
        _get_filtered_search_sample_data(request, sample_rows)
    )
    for row in filtered_rows:
        writer.writerow(
            [
                row["sequencing_id"],
                row["collection_date"],
                row["lineage"],
                row["collecting_institution"],
            ]
        )
    return response


def _get_collection_iso_week(collection_date):
    """Return ISO week in YYYY-WNN format from a collection date string."""
    if not collection_date:
        return ""
    try:
        parsed_date = datetime.strptime(collection_date, "%Y-%m-%d")
    except ValueError:
        return ""
    iso_year, iso_week, _ = parsed_date.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _get_epi_season(collection_date):
    """Return epidemiological season in YYYY_YYYY format."""
    if not collection_date:
        return ""
    try:
        parsed_date = datetime.strptime(collection_date, "%Y-%m-%d")
    except ValueError:
        return ""
    year, week, _weekday = parsed_date.isocalendar()
    if week >= 40:
        season_start = year
        season_end = year + 1
    else:
        season_start = year - 1
        season_end = year
    return f"{season_start}_{season_end}"



def _get_sample_lineage_value(sample, property_name):
    """Return a lineage value for the requested property name."""
    if not sample:
        return ""
    lineage_values = getattr(sample, "surveillance_lineages", None)
    if lineage_values is not None:
        for lineage_value in lineage_values:
            if lineage_value.lineage_fieldID.property_name == property_name:
                return lineage_value.value or ""
        return ""
    lineage_value = sample.lineage_values.filter(
        lineage_fieldID__property_name=property_name
    ).last()
    return lineage_value.value if lineage_value else ""


def _get_sample_bioinfo_value(sample, property_name):
    """Return a bioinfo analysis value for the requested property name."""
    if not sample:
        return ""
    bioinfo_values = getattr(sample, "surveillance_bioinfo_values", None)
    if bioinfo_values is not None:
        for bioinfo_value in bioinfo_values:
            if bioinfo_value.bioinfo_analysis_fieldID.property_name == property_name:
                return bioinfo_value.value or ""
        return ""
    bioinfo_value = sample.bio_analysis_values.filter(
        bioinfo_analysis_fieldID__property_name=property_name
    ).last()
    return bioinfo_value.value if bioinfo_value else ""


def _get_sample_public_database_value(sample, property_name):
    """Return a public database value for the requested property name."""
    if not sample:
        return ""
    public_database_values = getattr(sample, "surveillance_public_database_values", None)
    if public_database_values is not None:
        for public_database_value in public_database_values:
            if public_database_value.public_database_fieldID.property_name == property_name:
                return public_database_value.value or ""
        return ""
    public_database_value = sample.publicdatabasevalues_set.filter(
        public_database_fieldID__property_name=property_name
    ).last()
    return public_database_value.value if public_database_value else ""


@login_required
def search_sample_surveillance_data(request):
    """Download surveillance data for the currently filtered sample browser rows."""
    sample_rows = _get_search_sample_rows_for_user(request.user)
    filtered_rows = []
    if not (isinstance(sample_rows, dict) and "ERROR" in sample_rows):
        filtered_rows, _lineage_options, _institution_options = (
            _get_filtered_search_sample_data(request, sample_rows)
        )

    sequencing_ids = [row["sequencing_id"] for row in filtered_rows]
    lineage_prefetch = Prefetch(
        "lineage_values",
        queryset=core.models.LineageValues.objects.filter(
            lineage_fieldID__property_name__in=[
                "lineage_assignment",
                "lineage_assignment_software_version",
                "lineage_assignment_database_version",
            ]
        ).select_related("lineage_fieldID"),
        to_attr="surveillance_lineages",
    )
    bioinfo_prefetch = Prefetch(
        "bio_analysis_values",
        queryset=core.models.BioinfoAnalysisValue.objects.filter(
            bioinfo_analysis_fieldID__property_name__in=[
                "per_genome_greater_10x",
                "bioinformatics_analysis_date",
                "consensus_sequence_filename",
                "qc_test",
            ]
        ).select_related("bioinfo_analysis_fieldID"),
        to_attr="surveillance_bioinfo_values",
    )
    public_database_prefetch = Prefetch(
        "publicdatabasevalues_set",
        queryset=core.models.PublicDatabaseValues.objects.filter(
            public_database_fieldID__property_name="gisaid_accession_id"
        ).select_related("public_database_fieldID"),
        to_attr="surveillance_public_database_values",
    )
    sample_lookup = {
        sample.sequencing_sample_id: sample
        for sample in core.models.Sample.objects.filter(
            sequencing_sample_id__in=sequencing_ids
        ).prefetch_related(
            lineage_prefetch, bioinfo_prefetch, public_database_prefetch
        )
    }

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "per_sample_data"
    worksheet.append(
        [
            "COLLECTING_LAB_SAMPLE_ID",
            "SEQUENCING_SAMPLE_ID",
            "MICROBIOLOGY_LAB_SAMPLE_ID",
            "UNIQUE_SAMPLE_ID",
            "GISAID_ACCESSION_ID",
            "COLLECTING_INSTITUTION",
            "SUBMITTING_INSTITUTION",
            "SUBMITTING_INSTITUTION_ID",
            "CCAA",
            "PROVINCE",
            "SAMPLE_COLLECTION_DATE",
            "WEEK",
            "SEASON",
            "LINEAGE",
            "PANGOLIN_SOFTWARE_VERSION",
            "PANGOLIN_DATABASE_VERSION",
            "ANALYSIS_DATE",
            "COVERAGE_10X",
            "QC_TEST",
            "CONSENSUS_SEQUENCE_FILENAME",
        ]
    )
    for row in filtered_rows:
        sample = sample_lookup.get(row["sequencing_id"])
        iskylims_project_values = core.utils.samples.get_iskylims_project_values(
            sample
        )
        worksheet.append(
            [
                sample.collecting_lab_sample_id if sample else "",
                sample.sequencing_sample_id if sample else row["sequencing_id"],
                sample.microbiology_lab_sample_id if sample else "",
                sample.sample_unique_id if sample else "",
                _get_sample_public_database_value(sample, "gisaid_accession_id"),
                sample.collecting_institution if sample else "",
                sample.submitting_institution if sample else "",
                iskylims_project_values.get("Submitting Institution Identifier", ""),
                iskylims_project_values.get("Autonomic Community", ""),
                iskylims_project_values.get("Province", ""),
                row["collection_date"],
                _get_collection_iso_week(row["collection_date"]),
                _get_epi_season(row["collection_date"]),
                _get_sample_lineage_value(sample, "lineage_assignment"),
                _get_sample_lineage_value(
                    sample, "lineage_assignment_software_version"
                ),
                _get_sample_lineage_value(
                    sample, "lineage_assignment_database_version"
                ),
                _get_sample_bioinfo_value(sample, "bioinformatics_analysis_date"),
                _get_sample_bioinfo_value(sample, "per_genome_greater_10x"),
                _get_sample_bioinfo_value(sample, "qc_test"),
                _get_sample_bioinfo_value(sample, "consensus_sequence_filename"),
            ]
        )

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    response["Content-Disposition"] = 'attachment; filename="surveillance_data.xlsx"'
    return response


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


@login_required
def intranet(request):
    manager_group = Group.objects.filter(name="RelecovManager").last()
    all_sample_per_date_detailed = core.utils.samples.get_sample_per_date_per_all_lab(
        detailed=True
    )
    if "ERROR" in all_sample_per_date_detailed:
        return render(
            request,
            "core/intranet.html",
            {"ERROR": all_sample_per_date_detailed["ERROR"]},
        )
    clean_samples_per_date_detailed = []
    if manager_group not in request.user.groups.all():
        start = time.time()
        intra_data = {}
        user_role = core.utils.generic_functions.get_user_role(request.user)
        lab_name = core.utils.labs.get_lab_name_from_user(request.user)
        lab_code = None
        lab_codes = core.utils.labs.get_lab_codes_from_user(request.user)
        if lab_codes:
            lab_code = lab_codes[0]
        lab_field = core.utils.generic_functions.get_user_lab_field(request.user)
        if not lab_field:
            print(f"No institution field - group found for user: {str(request.user)}")
            return render(request, "core/intranet.html", {"intra_data": {}})
        counted_dates = defaultdict(int)
        for d in all_sample_per_date_detailed:
            value = d.get(lab_field)
            matches_lab = False
            if user_role == "Collector":
                if lab_code and value == lab_code:
                    matches_lab = True
                else:
                    fallback_name = (
                        d.get("legacy_collecting_institution")
                        or d.get("collecting_institution")
                        or ""
                    )
                    if lab_name and fallback_name:
                        matches_lab = fallback_name.lower() == lab_name.lower()
                if not matches_lab:
                    continue
            else:
                if not value or not lab_name or value.lower() != lab_name.lower():
                    continue
            # Adapt YYYY-WNN to datetime format so it can be converted to date object
            converted_date = datetime.strptime(d["iso_yearweek"] + "-1", "%G-W%V-%u")
            # Filter out old data
            if converted_date.year < 2019:
                continue
            counted_dates[d["iso_yearweek"]] += d["num_samples"]
            clean_samples_per_date_detailed.append(
                {k: v for k, v in d.items() if k != "submitting_institution"}
            )
        dates_sorted = sorted(
            counted_dates.keys(),
            key=lambda x: datetime.strptime(x + "-1", "%G-W%V-%u"),
        )
        date_lab_samples = OrderedDict({k: counted_dates[k] for k in dates_sorted})
        display_lab_name = (
            core.utils.labs.get_display_name_from_code(lab_code)
            if lab_code
            else lab_name
        )
        intra_data["lab"] = display_lab_name
        print(f"Took {start - time.time()} seconds for date_lab_samples")
        if len(date_lab_samples) > 0:
            start = time.time()
            sample_lab_objs = core.utils.samples.get_sample_objs_per_lab(lab_name)
            print(f"Took {start - time.time()} seconds for sample_lab_objs")
            analysis_lab_name = (
                lab_code if user_role == "Collector" and lab_code else lab_name
            )
            analysis_percent = (
                core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab(
                    lab_name=analysis_lab_name, institution_type=lab_field
                )
            )
            print(f"Took {start - time.time()} seconds for analysis_percent")
            cust_data = {
                "col_names": ["Collecting Date", "Number of samples"],
                "options": {},
            }
            cust_data["options"][
                "title"
            ] = f"Samples Received: {sum(date_lab_samples.values())}"
            cust_data["options"]["width"] = 600
            intra_data["sample_bar_graph"] = core.utils.samples.create_date_sample_bar(
                date_lab_samples, cust_data
            )
            print(f"Took {start - time.time()} seconds for sample_bar_graph")
            intra_data["sample_gauge_graph"] = core.utils.samples.fancy_gauge_graphic(
                value=(
                    analysis_percent["analized"] / analysis_percent["received"] * 100
                    if analysis_percent["received"]
                    else 0
                )
            )
            lablist = []
            seen_values = set()
            for entry in clean_samples_per_date_detailed:
                code = entry.get("lab_code_1")
                display = entry.get("collecting_institution") or entry.get(
                    "legacy_collecting_institution"
                )
                value = code or display
                if not value or value in seen_values:
                    continue
                seen_values.add(value)
                label = (
                    core.utils.labs.get_display_name_from_code(code)
                    if code
                    else display
                )
                lablist.append({"value": value, "label": label or value})
            if len(lablist) > 1:
                intra_data["sample_per_lab_initial_arguments"] = (
                    core.utils.samples.create_dash_bar_for_each_lab(
                        clean_samples_per_date_detailed, lablist
                    )
                )
                intra_data["show_per_lab_dash"] = True
            else:
                intra_data["show_per_lab_dash"] = False
            print(f"Took {start - time.time()} seconds for gauge_graph")
            intra_data["actions"] = core.utils.samples.get_lab_last_actions(lab_name)
            gisaid_acc = core.utils.public_db.get_preprocessed_gisaid_data()
            # NOTE: Filters by lab_name instead of sample_lab_objs to improve performance, but could lead to mismatches
            print(f"Took {start - time.time()} seconds for gisaid data")
            if gisaid_acc:
                gisaid_acc_filtered = gisaid_acc.get(lab_name, [])
                intra_data["gisaid_accession"] = gisaid_acc_filtered
                intra_data["gisaid_graph"] = core.utils.public_db.percentage_graphic(
                    len(sample_lab_objs), len(gisaid_acc_filtered), ""
                )
            print(f"Took {start - time.time()} seconds for gisaig graph")
            ena_acc = core.utils.public_db.get_preprocessed_ena_data()
            if ena_acc:
                ena_acc_filtered = ena_acc.get(lab_name, [])
                intra_data["ena_accession"] = ena_acc_filtered
                intra_data["ena_graph"] = core.utils.public_db.percentage_graphic(
                    len(sample_lab_objs), len(ena_acc_filtered), ""
                )
            print(f"Took {start - time.time()} seconds for ena graph")
        return render(request, "core/intranet.html", {"intra_data": intra_data})
    else:
        # loged user belongs to Relecov Manager group
        manager_intra_data = {}
        all_sample_per_date_detailed = (
            core.utils.samples.get_sample_per_date_per_all_lab(detailed=True)
        )
        num_of_samples = core.utils.samples.count_handled_samples()
        if len(all_sample_per_date_detailed) > 0:
            counted_dates = defaultdict(int)
            clean_samples_per_date_detailed = []

            for d in all_sample_per_date_detailed:
                try:
                    converted_date = datetime.strptime(
                        d["iso_yearweek"] + "-1", "%G-W%V-%u"
                    )
                    if converted_date.year < 2019:
                        continue
                except Exception:
                    print(f"Error parsing iso_yearweek: {d['iso_yearweek']}")
                    continue

                counted_dates[d["iso_yearweek"]] += d["num_samples"]
                clean_samples_per_date_detailed.append(
                    {k: v for k, v in d.items() if k != "submitting_institution"}
                )

            dates_sorted = sorted(
                counted_dates.keys(),
                key=lambda x: datetime.strptime(x + "-1", "%G-W%V-%u"),
            )
            date_samples_all = OrderedDict({k: counted_dates[k] for k in dates_sorted})

            cust_data = {
                "col_names": ["Collecting Date", "Number of samples"],
                "options": {},
            }
            cust_data["options"]["title"] = cust_data["options"]["title"] = (
                f"Samples Received for all laboratories: {sum(date_samples_all.values())}"
            )
            cust_data["options"]["width"] = 590
            manager_intra_data["sample_bar_graph"] = (
                core.utils.samples.create_date_sample_bar(date_samples_all, cust_data)
            )
            # graph for percentage analysis
            analysis_percent = (
                core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab()
            )
            manager_intra_data["sample_gauge_graph"] = (
                core.utils.samples.fancy_gauge_graphic(
                    value=(
                        analysis_percent["analized"]
                        / analysis_percent["received"]
                        * 100
                        if analysis_percent["received"]
                        else 0
                    )
                )
            )
            all_labs = core.utils.samples.get_all_collecting_insts()
            # dash graph for samples per all lab
            clean_samples_per_date_detailed = [
                {k: v for k, v in d.items() if k != "submitting_institution"}
                for d in all_sample_per_date_detailed
            ]
            manager_intra_data["sample_per_lab_initial_arguments"] = (
                core.utils.samples.create_dash_bar_for_each_lab(
                    clean_samples_per_date_detailed, all_labs
                )
            )
            # Get the latest action from each lab
            manager_intra_data["actions"] = core.utils.samples.get_lab_last_actions()
            # Collect GISAID information
            gisaid_acc = core.utils.public_db.get_preprocessed_gisaid_data()
            full_gisaid_data = [
                (lab, *tup) for lab, tuples in gisaid_acc.items() for tup in tuples
            ]
            if len(gisaid_acc) > 0:
                manager_intra_data["gisaid_accession"] = full_gisaid_data
                manager_intra_data["gisaid_graph"] = (
                    core.utils.public_db.percentage_graphic(
                        num_of_samples["Defined"], len(full_gisaid_data), ""
                    )
                )
            # Collect Ena information
            ena_acc = core.utils.public_db.get_preprocessed_ena_data()
            full_ena_data = [
                (lab, *tup) for lab, tuples in ena_acc.items() for tup in tuples
            ]
            if len(ena_acc) > 0:
                manager_intra_data["ena_accession"] = full_ena_data
                manager_intra_data["ena_graph"] = (
                    core.utils.public_db.percentage_graphic(
                        num_of_samples["Defined"], len(full_ena_data), ""
                    )
                )
        return render(
            request,
            "core/intranet.html",
            {"manager_intra_data": manager_intra_data},
        )


def variants(request):
    return render(request, "core/variants.html", {})


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


@login_required()
def laboratory_contact(request):
    lab_data = core.utils.labs.get_lab_contact_details(request.user)
    user_lab = core.utils.labs.get_lab_name_from_user(request.user)
    proc_lab_data = {k.replace(" ", "_").lower(): v for k, v in lab_data.items()}
    if "ERROR" in lab_data:
        return render(
            request,
            "core/laboratoryContact.html",
            {
                "ERROR": f"{lab_data['ERROR']} : No contact data found for your laboratory {user_lab}",
                "lab_data": proc_lab_data,
            },
        )
    if request.method == "POST" and request.POST["action"] == "updateLabData":
        result = core.utils.labs.update_contact_lab(request.POST)
        if isinstance(result, dict):
            errdict = {
                "ERROR": f"{result['ERROR']} - Could not update your contact details",
                "lab_data": proc_lab_data,
            }
            return render(request, "core/laboratoryContact.html", errdict)
        updated_data = {
            k: (request.POST.get(k) if request.POST.get(k) else v)
            for k, v in proc_lab_data.items()
        }
        return render(
            request,
            "core/laboratoryContact.html",
            {"Success": "Success", "lab_data": updated_data},
        )
    return render(request, "core/laboratoryContact.html", {"lab_data": proc_lab_data})


@login_required
def received_samples(request):
    sample_data = {}
    # samples receive over time map
    sample_data["map"] = core.utils.samples_map.create_samples_received_map()

    # # collecting now data from database
    sample_data["received_samples_graph"] = (
        core.utils.samples_graphics.received_samples_graph()
    )
    # Pie charts
    sample_data["samples_per_ccaa"] = core.utils.samples_graphics.received_per_ccaa()
    # create_samples_received_over_time_per_laboratory_pieChart(data)
    sample_data["samples_per_lab"] = core.utils.samples_graphics.received_per_lab()
    return render(
        request,
        "core/receivedSamples.html",
        {"sample_data": sample_data},
    )


def contact(request):
    contact_data = {
        "email": "bioinformatica@isciii.es",
        "telephone": "(+34) 91 822 37 95",
    }
    return render(request, "core/contact.html", {"contact_data": contact_data})
