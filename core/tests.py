import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pandas as pd
from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.test import RequestFactory, SimpleTestCase, TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

import core.api.utils.samples
import core.api.utils.bioinfo_metadata
import core.api.utils.common_functions
import core.api.utils.public_db
import core.api.utils.variants
import core.api.views
import core.models
import core.utils.annotation
import core.utils.bioinfo_analysis
import core.utils.generic_functions
import core.utils.lab_catalog
import core.utils.labs
import core.utils.lineage
import core.utils.plotly_dash_graphics
import core.utils.public_db
import core.utils.rest_api
import core.utils.samples
import core.utils.samples_graphics
import core.utils.schema
import core.utils.variants
from core.templatetags.user_groups import has_group
from core.views import (
    _get_search_sample_rows_for_user,
    _get_sort_value,
    _normalize_datatable_search_value,
    _row_matches_search,
    search_sample_data,
)


class SearchSampleFilteringTests(SimpleTestCase):
    def test_normalizes_escaped_exact_match_regex(self):
        self.assertEqual(
            _normalize_datatable_search_value(r"^XFG\.3$", regex=True),
            "XFG.3",
        )

    def test_combines_institution_and_lineage_exact_filters(self):
        row = {
            "sequencing_id": "sample-1",
            "collection_date": "2026-01-01",
            "lineage": "XFG.3",
            "collecting_institution": (
                "Complejo Hospitalario San Pedro Hospital De La Rioja"
            ),
        }
        column_filters = [
            ("lineage", _normalize_datatable_search_value(r"^XFG\.3$", True), True),
            (
                "collecting_institution",
                _normalize_datatable_search_value(
                    "^Complejo Hospitalario San Pedro Hospital De La Rioja$", True
                ),
                True,
            ),
        ]

        self.assertTrue(_row_matches_search(row, "", column_filters))

    @patch("core.views._get_search_sample_rows_for_user")
    def test_server_side_endpoint_filters_sorts_and_paginates(self, get_rows):
        get_rows.return_value = [
            {
                "id": 1,
                "sequencing_id": "SEQ-002",
                "collection_date": "2026-01-02",
                "lineage": "XFG.3",
                "collecting_institution": "Hospital A",
            },
            {
                "id": 2,
                "sequencing_id": "SEQ-001",
                "collection_date": "2026-01-01",
                "lineage": "XFG.3",
                "collecting_institution": "Hospital A",
            },
            {
                "id": 3,
                "sequencing_id": "SEQ-003",
                "collection_date": "2026-01-03",
                "lineage": "JN.1",
                "collecting_institution": "Hospital B",
            },
        ]
        request = RequestFactory().get(
            "/searchSample/data",
            {
                "draw": "7",
                "start": "1",
                "length": "1",
                "columns[2][search][value]": "XFG.3",
                "columns[2][search][regex]": "false",
                "columns[3][search][value]": "Hospital A",
                "columns[3][search][regex]": "false",
                "order[0][column]": "0",
                "order[0][dir]": "asc",
            },
        )
        request.user = SimpleNamespace(is_authenticated=True)

        response = search_sample_data(request)
        payload = json.loads(response.content)

        self.assertEqual(payload["draw"], 7)
        self.assertEqual(payload["recordsTotal"], 3)
        self.assertEqual(payload["recordsFiltered"], 2)
        self.assertEqual([row["sequencing_id"] for row in payload["data"]], ["SEQ-002"])


class GenericFunctionTests(SimpleTestCase):
    def test_date_validation(self):
        self.assertTrue(
            core.utils.generic_functions.check_valid_date_format("2026-06-23")
        )
        self.assertFalse(
            core.utils.generic_functions.check_valid_date_format("23/06/2026")
        )

    def test_week_generation_includes_both_bounds(self):
        weeks = core.utils.generic_functions.list_all_possible_weeks(
            datetime(2026, 1, 5),
            datetime(2026, 1, 19),
            "%Y-%m-%d",
        )

        self.assertEqual(weeks, ["2026-01-05", "2026-01-12", "2026-01-19"])

    def test_unique_sample_id_rolls_over_number_and_letters(self):
        self.assertEqual(
            core.utils.samples.increase_unique_value("RLCV-AAA-9999"),
            "RL-AAB-0001",
        )


class LabCatalogTests(SimpleTestCase):
    def tearDown(self):
        core.utils.lab_catalog._build_name_index.cache_clear()

    @patch("core.utils.lab_catalog._load_catalog")
    def test_resolves_codes_and_names_case_insensitively(self, load_catalog):
        load_catalog.return_value = {
            "LAB-01": {"collecting_institution": "Hospital Example"}
        }
        core.utils.lab_catalog._build_name_index.cache_clear()

        self.assertEqual(
            core.utils.lab_catalog.get_lab_code("hospital example"),
            "LAB-01",
        )
        self.assertEqual(
            core.utils.lab_catalog.get_lab_name("LAB-01"),
            "Hospital Example",
        )

    @patch("core.utils.lab_catalog.get_lab_name", return_value="")
    def test_display_falls_back_to_provided_name_or_code(self, _get_lab_name):
        self.assertEqual(
            core.utils.lab_catalog.ensure_lab_display("UNKNOWN", "Legacy Hospital"),
            "Legacy Hospital",
        )
        self.assertEqual(
            core.utils.lab_catalog.ensure_lab_display("UNKNOWN"),
            "UNKNOWN",
        )


class PlotlyDashGraphicTests(SimpleTestCase):
    class FakeDashApp:
        def __init__(self):
            self.layout = None
            self.callbacks = []

        def callback(self, *args, **kwargs):
            def decorator(function):
                self.callbacks.append(function)
                return function

            return decorator

    def build_app(self, options, data):
        fake_app = self.FakeDashApp()
        patcher = patch(
            "core.utils.plotly_dash_graphics.DjangoDash",
            return_value=fake_app,
        )
        with patcher as django_dash:
            core.utils.plotly_dash_graphics.dash_bar_lab(options, data)
        return fake_app, django_dash

    def get_dropdown(self, fake_app):
        return fake_app.layout.children[1].children[0]

    def test_dash_bar_lab_normalizes_options_and_registers_layout(self):
        data = pd.DataFrame(
            {
                "lab_code_1": ["LAB-01"],
                "collecting_institution": ["Hospital A"],
                "iso_yearweek": ["2024-W01"],
                "num_samples": [1],
            }
        )

        fake_app, django_dash = self.build_app(
            [
                {"label": "Hospital A", "value": "LAB-01"},
                {"collecting_institution": "Hospital B", "lab_code_1": "LAB-02"},
                {"legacy_name": "Legacy Hospital"},
                {"value": ""},
                {"label": "Duplicate Hospital A", "value": "LAB-01"},
                "Free Text Hospital",
            ],
            data,
        )

        dropdown = self.get_dropdown(fake_app)
        self.assertEqual(
            dropdown.options,
            [
                {"label": "Hospital A", "value": "LAB-01"},
                {"label": "Hospital B", "value": "LAB-02"},
                {"label": "Legacy Hospital", "value": "Legacy Hospital"},
                {"label": "Free Text Hospital", "value": "Free Text Hospital"},
            ],
        )
        self.assertEqual(dropdown.value, "LAB-01")
        self.assertEqual(len(fake_app.callbacks), 1)
        django_dash.assert_called_once()

    def test_dash_bar_lab_without_options_uses_no_default_value(self):
        fake_app, _django_dash = self.build_app(
            [],
            pd.DataFrame(
                {
                    "lab_code_1": ["LAB-01"],
                    "iso_yearweek": ["2024-W01"],
                    "num_samples": [1],
                }
            ),
        )

        self.assertIsNone(self.get_dropdown(fake_app).value)

    def test_dash_bar_callback_filters_by_lab_code_and_formats_sorted_weeks(self):
        data = pd.DataFrame(
            {
                "lab_code_1": ["LAB-01", "LAB-01", "LAB-01", "LAB-02"],
                "collecting_institution": [
                    "Hospital A",
                    "Hospital A",
                    "Hospital A",
                    "Hospital B",
                ],
                "legacy_collecting_institution": [
                    "Legacy A",
                    "Legacy A",
                    "Legacy A",
                    "Legacy B",
                ],
                "iso_yearweek": ["2024-W2", "2024-W1", "2024-W1", "2024-W3"],
                "num_samples": ["5", "2", "99", "7"],
            }
        )
        fake_app, _django_dash = self.build_app(
            [{"label": "Hospital A", "value": "LAB-01"}],
            data,
        )

        figure = fake_app.callbacks[0]("LAB-01")

        self.assertEqual(list(figure.data[0].x), ["2024-W01", "2024-W02"])
        self.assertEqual(list(figure.data[0].y), [2, 5])
        self.assertEqual(figure.layout.title.text, "Registered samples over time")
        self.assertEqual(figure.layout.xaxis.title.text, "Collecting date (ISOWeeks)")
        self.assertEqual(figure.layout.yaxis.title.text, "Number of samples")

    def test_dash_bar_callback_filters_by_fallback_lab_names(self):
        data = pd.DataFrame(
            {
                "lab_code_1": [None, None, "LAB-02"],
                "collecting_institution": ["Hospital A", "Hospital C", "Hospital B"],
                "legacy_collecting_institution": ["Legacy A", "Legacy C", "Legacy B"],
                "iso_yearweek": ["2024-W1", "2024-W2", "2024-W3"],
                "num_samples": [4, 6, 8],
            }
        )
        fake_app, _django_dash = self.build_app(
            [{"label": "Hospital A", "value": "Hospital A"}],
            data,
        )

        by_collecting_name = fake_app.callbacks[0]("Hospital A")
        by_legacy_name = fake_app.callbacks[0]("Legacy C")

        self.assertEqual(list(by_collecting_name.data[0].y), [4])
        self.assertEqual(list(by_legacy_name.data[0].x), ["2024-W02"])
        self.assertEqual(list(by_legacy_name.data[0].y), [6])

    def test_dash_bar_callback_filters_when_only_collecting_institution_exists(self):
        data = pd.DataFrame(
            {
                "collecting_institution": ["Hospital A", "Hospital B"],
                "iso_yearweek": ["2024-W1", "2024-W2"],
                "num_samples": [3, 9],
            }
        )
        fake_app, _django_dash = self.build_app(["Hospital B"], data)

        figure = fake_app.callbacks[0]("Hospital B")

        self.assertEqual(list(figure.data[0].x), ["2024-W02"])
        self.assertEqual(list(figure.data[0].y), [9])

    def test_dash_bar_callback_handles_empty_selection_and_missing_data_columns(self):
        data = pd.DataFrame(
            {
                "iso_yearweek": ["2024-W1"],
                "num_samples": [3],
            }
        )
        fake_app, _django_dash = self.build_app(["Hospital A"], data)

        with self.assertRaises(core.utils.plotly_dash_graphics.PreventUpdate):
            fake_app.callbacks[0](None)

        figure = fake_app.callbacks[0]("Hospital A")

        self.assertEqual(
            figure.layout.title.text,
            "No data available for the selected laboratory",
        )


class SampleApiUtilityTests(SimpleTestCase):
    @patch(
        "core.api.utils.samples.core.utils.samples.get_user_id_from_submitting_institution"
    )
    @patch("core.api.utils.samples.core.models.Sample.objects")
    @patch("core.api.utils.samples.core.models.SampleState.objects")
    def test_split_sample_data_normalizes_aliases_dates_and_sections(
        self,
        state_manager,
        sample_manager,
        get_user_id,
    ):
        state = MagicMock()
        state.get_state_id.return_value = "1"
        state_manager.filter.return_value.last.return_value = state
        sample_manager.all.return_value.exists.return_value = False
        get_user_id.return_value = 42

        result = core.api.utils.samples.split_sample_data(
            {
                "sequencing_sample_id": "SEQ-1",
                "submitting_institution": "Submitter A",
                "collecting_institution_code_1": "LAB-01",
                "sequencing_date": "20260623",
                "author_submitter": "A. Scientist",
                "gisaid_id": "EPI_ISL_1",
                "ena_sample_accession": "ERS1",
            }
        )

        self.assertEqual(result["sample"]["lab_code_1"], "LAB-01")
        self.assertEqual(result["sample"]["sequencing_date"], datetime(2026, 6, 23))
        self.assertEqual(result["sample"]["sample_unique_id"], "RL-AAA-0001")
        self.assertEqual(result["sample"]["user"], 42)
        self.assertEqual(result["author"], {"author_submitter": "A. Scientist"})
        self.assertEqual(result["gisaid"], {"gisaid_id": "EPI_ISL_1"})
        self.assertEqual(result["ena"], {"ena_sample_accession": "ERS1"})

    def test_fingerprint_is_case_insensitive_and_stable(self):
        upper = core.utils.samples.build_sample_fingerprint(
            "SEQ-1", "COL-1", "Submitter", "Collector"
        )
        lower = core.utils.samples.build_sample_fingerprint(
            "seq-1", "col-1", "submitter", "collector"
        )

        self.assertEqual(upper, lower)
        self.assertEqual(len(upper), 24)


class SearchSummaryAuthorizationTests(SimpleTestCase):
    summary = {
        "Submitter A": {
            "LAB-01": {
                "lab_code_1": "LAB-01",
                "collecting_institution": "Hospital A",
                "rows": [[1, "SEQ-1", "2026-01-01", "XFG.3", "Hospital A"]],
            }
        },
        "Submitter B": {
            "LAB-02": {
                "lab_code_1": "LAB-02",
                "collecting_institution": "Hospital B",
                "rows": [[2, "SEQ-2", "2026-01-02", "JN.1", "Hospital B"]],
            }
        },
    }

    @patch(
        "core.utils.samples.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    @patch("core.utils.samples.core.utils.generic_functions.get_user_role")
    def test_manager_sees_all_cached_rows(self, get_role, get_graphic):
        get_role.return_value = "RelecovManager"
        get_graphic.return_value = self.summary

        rows = core.utils.samples.get_search_table_for_user(
            SimpleNamespace(username="manager")
        )

        self.assertEqual([row[1] for row in rows], ["SEQ-1", "SEQ-2"])

    @patch(
        "core.utils.samples.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    @patch("core.utils.samples.core.utils.labs.get_lab_name_from_user")
    @patch("core.utils.samples.core.utils.generic_functions.get_user_role")
    def test_submitter_only_sees_its_rows(self, get_role, get_lab_name, get_graphic):
        get_role.return_value = "Submitter"
        get_lab_name.return_value = "Submitter B"
        get_graphic.return_value = self.summary

        rows = core.utils.samples.get_search_table_for_user(
            SimpleNamespace(username="submitter")
        )

        self.assertEqual([row[1] for row in rows], ["SEQ-2"])

    @patch(
        "core.utils.samples.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    @patch("core.utils.samples.core.utils.labs.get_lab_name_from_user")
    @patch("core.utils.samples.core.utils.labs.get_lab_codes_from_user")
    @patch("core.utils.samples.core.utils.generic_functions.get_user_role")
    def test_collector_is_matched_by_lab_code(
        self,
        get_role,
        get_lab_codes,
        get_lab_name,
        get_graphic,
    ):
        get_role.return_value = "Collector"
        get_lab_codes.return_value = ["LAB-01"]
        get_lab_name.return_value = "Renamed Hospital"
        get_graphic.return_value = self.summary

        rows = core.utils.samples.get_search_table_for_user(
            SimpleNamespace(username="collector")
        )

        self.assertEqual([row[1] for row in rows], ["SEQ-1"])


class ApiValidationTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(pk=1, is_authenticated=True)

    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists",
        return_value=None,
    )
    def test_create_sample_rejects_unknown_schema(self, _get_schema):
        request = self.factory.post(
            "/api/createSampleData",
            {"schema_name": "unknown", "schema_version": "0"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = core.api.views.create_sample_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["ERROR"], "schema name and version is not defined"
        )

    @patch("core.api.views.core.utils.lab_catalog.ensure_lab_display", return_value="")
    def test_check_sample_exists_reports_missing_identifiers(self, _display):
        request = self.factory.get(
            "/api/checkSampleExists",
            {"sequencing_sample_id": "SEQ-1"},
        )
        force_authenticate(request, user=self.user)

        response = core.api.views.check_sample_exists(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("collecting_lab_sample_id", response.data["ERROR"])
        self.assertIn("submitting_institution", response.data["ERROR"])

    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_fingerprint",
        return_value=None,
    )
    @patch(
        "core.api.views.core.utils.lab_catalog.ensure_lab_display",
        return_value="Hospital A",
    )
    def test_check_sample_exists_uses_canonical_fingerprint(
        self,
        _display,
        get_sample,
    ):
        request = self.factory.get(
            "/api/checkSampleExists",
            {
                "sequencing_sample_id": "SEQ-1",
                "collecting_lab_sample_id": "COL-1",
                "submitting_institution": "Submitter A",
                "collecting_institution_code_1": "LAB-01",
            },
        )
        force_authenticate(request, user=self.user)

        response = core.api.views.check_sample_exists(request)

        expected = core.utils.samples.build_sample_fingerprint(
            "SEQ-1", "COL-1", "Submitter A", "Hospital A"
        )
        get_sample.assert_called_once_with(expected)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Sample not found.")

    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_sample_name",
        return_value=None,
    )
    def test_update_state_rejects_unknown_sample(self, _get_sample):
        request = self.factory.put(
            "/api/updateState",
            {"sample_name": "missing", "state": "Bioinfo"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = core.api.views.update_state(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["ERROR"], core.config.ERROR_SAMPLE_NOT_DEFINED)


class CoreModelIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.defined = core.models.SampleState.objects.create(
            state="Defined",
            display_string="Defined",
        )

    def create_user(self, username, role, laboratory="", code=""):
        user = User.objects.create_user(username=username, password="test-password")
        user.groups.add(Group.objects.create(name=role))
        core.models.Profile.objects.filter(user=user).update(
            laboratory=laboratory,
            code_id=code,
        )
        return user

    def create_sample(
        self,
        seq_id,
        collecting_id,
        submitter,
        collector,
        code="",
    ):
        return core.models.Sample.objects.create(
            state=self.defined,
            sample_unique_id=f"RLCV-{seq_id}",
            sequencing_sample_id=seq_id,
            collecting_lab_sample_id=collecting_id,
            submitting_institution=submitter,
            collecting_institution=collector,
            lab_code_1=code,
        )

    def test_user_creation_also_creates_profile(self):
        user = User.objects.create_user(username="profile-user")

        self.assertTrue(core.models.Profile.objects.filter(user=user).exists())

    def test_sample_save_generates_fingerprint_and_rejects_duplicate_identity(self):
        sample = self.create_sample(
            "SEQ-1", "COL-1", "Submitter A", "Hospital A", "LAB-01"
        )

        self.assertEqual(
            sample.sample_fingerprint,
            core.utils.samples.build_sample_fingerprint(
                "SEQ-1", "COL-1", "Submitter A", "Hospital A"
            ),
        )
        with self.assertRaises(IntegrityError):
            self.create_sample("seq-1", "col-1", "submitter a", "hospital a", "LAB-01")

    def test_schema_manager_keeps_only_latest_selected_default(self):
        user = User.objects.create_user(username="schema-owner")
        first = core.models.Schema.objects.create_new_schema(
            {
                "file_name": "schemas/first.json",
                "user_name": user,
                "schema_name": "RELECOV",
                "schema_version": "1",
                "schema_default": True,
                "schema_app_name": "core",
            }
        )
        second = core.models.Schema.objects.create_new_schema(
            {
                "file_name": "schemas/second.json",
                "user_name": user,
                "schema_name": "RELECOV",
                "schema_version": "2",
                "schema_default": True,
                "schema_app_name": "core",
            }
        )

        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.schema_default)
        self.assertTrue(second.schema_default)

    def test_available_samples_are_isolated_by_role_and_lab(self):
        manager = self.create_user("manager", "RelecovManager")
        submitter = self.create_user("submitter", "Submitter", laboratory="Submitter A")
        collector = self.create_user(
            "collector", "Collector", laboratory="Hospital A", code="LAB-01"
        )
        first = self.create_sample(
            "SEQ-1", "COL-1", "Submitter A", "Hospital A", "LAB-01"
        )
        second = self.create_sample(
            "SEQ-2", "COL-2", "Submitter B", "Hospital B", "LAB-02"
        )

        self.assertCountEqual(
            core.utils.samples.get_available_samples_for_user(manager),
            [first, second],
        )
        self.assertCountEqual(
            core.utils.samples.get_available_samples_for_user(submitter),
            [first],
        )
        self.assertCountEqual(
            core.utils.samples.get_available_samples_for_user(collector),
            [first],
        )

    def test_lineage_list_excludes_empty_and_unassigned_values(self):
        field = core.models.LineageFields.objects.create(
            property_name="lineage_assignment",
            label_name="Lineage",
        )
        for value in ["XFG.3", "JN.1", "Unassigned", "Not Provided"]:
            core.models.LineageValues.objects.create(
                lineage_fieldID=field,
                value=value,
            )

        self.assertEqual(core.utils.lineage.get_lineages_list(), ["JN.1", "XFG.3"])


class SchemaUtilityIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="schema-test-owner")
        cls.schema = core.models.Schema.objects.create_new_schema(
            {
                "file_name": "schemas/test.json",
                "user_name": cls.user,
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "schema_default": True,
                "schema_app_name": "core",
            }
        )

    def test_schema_property_storage_creates_classification_and_options(self):
        properties = {
            "host_sex": {
                "examples": "Female",
                "ontology": "GENEPIO:0001234",
                "type": "string",
                "description": "Host sex",
                "label": "Host Sex",
                "classification": "Host Information",
                "fill_mode": "sample",
                "enum": ["Female [NCIT:C16576]", "Unknown"],
            }
        }

        result = core.utils.schema.store_schema_properties(
            self.schema,
            properties,
            required=["host_sex"],
        )

        prop = core.models.SchemaProperties.objects.get(property="host_sex")
        self.assertEqual(result, {"SUCCESS": ""})
        self.assertTrue(prop.required)
        self.assertTrue(prop.options)
        self.assertEqual(prop.get_classification(), "Host Information")
        self.assertCountEqual(
            core.models.PropertyOptions.objects.filter(propertyID=prop).values_list(
                "enum", "ontology"
            ),
            [("Female", "NCIT:C16576"), ("Unknown", None)],
        )

    def test_schema_field_classifications_create_specialized_fields(self):
        properties = {
            "depth_of_coverage_value": {
                "classification": "Bioinformatic analysis",
                "label": "Depth",
            },
            "lineage_assignment": {
                "classification": "Lineage fields",
                "label": "Lineage",
            },
            "other_field": {
                "classification": "Host Information",
                "label": "Other",
            },
        }

        core.utils.schema.store_bioinfo_fields(self.schema, properties)
        core.utils.schema.store_lineage_fields(self.schema, properties)

        self.assertTrue(
            core.models.BioinfoAnalysisField.objects.filter(
                property_name="depth_of_coverage_value",
                schemaID=self.schema,
            ).exists()
        )
        self.assertTrue(
            core.models.LineageFields.objects.filter(
                property_name="lineage_assignment",
                schemaID=self.schema,
            ).exists()
        )
        self.assertFalse(
            core.models.BioinfoAnalysisField.objects.filter(
                property_name="other_field"
            ).exists()
        )

    def test_metadata_visualization_replaces_previous_selection(self):
        core.models.MetadataVisualization.objects.create_metadata_visualization(
            {
                "schema_id": self.schema,
                "property_name": "old",
                "label_name": "Old field",
                "order": 0,
                "in_use": True,
                "fill_mode": "sample",
            }
        )
        payload = {
            "schemaID": str(self.schema.pk),
            "table_data": json.dumps(
                [
                    ["field_a", "Field A", 1, True, "sample"],
                    ["field_b", "Field B", "", True, "batch"],
                ]
            ),
        }

        result = core.utils.schema.store_fields_metadata_visualization(payload)

        self.assertEqual(result, {"SUCCESS": 1})
        self.assertEqual(
            list(
                core.models.MetadataVisualization.objects.values_list(
                    "property_name", flat=True
                )
            ),
            ["field_a"],
        )

    def test_invalid_schema_heading_is_rejected(self):
        self.assertFalse(
            core.utils.schema.check_heading_valid_json(
                {"type": "object"},
                core.config.MAIN_SCHEMA_STRUCTURE,
            )
        )
        self.assertTrue(
            core.utils.schema.check_heading_valid_json(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "required": [],
                    "type": "object",
                    "properties": {},
                },
                core.config.MAIN_SCHEMA_STRUCTURE,
            )
        )


class BioinfoStorageIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="bioinfo-owner")
        cls.state = core.models.SampleState.objects.create(state="Defined")
        cls.schema = core.models.Schema.objects.create_new_schema(
            {
                "file_name": "schemas/bioinfo.json",
                "user_name": cls.user,
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "schema_default": True,
                "schema_app_name": "core",
            }
        )
        cls.sample = core.models.Sample.objects.create(
            state=cls.state,
            sample_unique_id="RL-BIO-0001",
            sequencing_sample_id="BIO-1",
            collecting_lab_sample_id="COL-BIO-1",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )
        cls.bio_field = core.models.BioinfoAnalysisField.objects.create(
            property_name="bioinformatics_analysis_date",
            label_name="Analysis date",
        )
        cls.bio_field.schemaID.add(cls.schema)
        cls.lineage_field = core.models.LineageFields.objects.create(
            property_name="lineage_assignment",
            label_name="Lineage",
        )
        cls.lineage_field.schemaID.add(cls.schema)

    def test_split_and_store_bioinfo_links_values_to_target_sample(self):
        split_data = core.api.utils.bioinfo_metadata.split_bioinfo_data(
            {
                "unique_sample_id": self.sample.sample_unique_id,
                "bioinformatics_analysis_date": "2026-06-23",
                "lineage_assignment": "XFG.3",
                "ignored": "value",
            },
            self.schema,
        )

        result = core.api.utils.bioinfo_metadata.store_bioinfo_data(
            split_data,
            self.schema,
        )

        self.assertEqual(result, {"SUCCESS": "success"})
        self.assertEqual(
            list(self.sample.bio_analysis_values.values_list("value", flat=True)),
            ["2026-06-23"],
        )
        self.assertEqual(
            list(self.sample.lineage_values.values_list("value", flat=True)),
            ["XFG.3"],
        )
        self.assertNotIn("ignored", split_data["bioinfo"])

    def test_store_bioinfo_rejects_missing_sample_and_duplicate_analysis(self):
        missing = core.api.utils.bioinfo_metadata.store_bioinfo_data(
            {
                "unique_sample_id": "missing",
                "bioinfo": {"bioinformatics_analysis_date": "2026-06-23"},
            },
            self.schema,
        )
        value = core.models.BioinfoAnalysisValue.objects.create(
            value="2026-06-23",
            bioinfo_analysis_fieldID=self.bio_field,
        )
        self.sample.bio_analysis_values.add(value)
        duplicate = core.api.utils.bioinfo_metadata.store_bioinfo_data(
            {
                "unique_sample_id": self.sample.sample_unique_id,
                "bioinfo": {"bioinformatics_analysis_date": "2026-06-23"},
            },
            self.schema,
        )

        self.assertIn("Sample not found", missing["ERROR"])
        self.assertEqual(
            duplicate,
            {"ERROR": "Analysis already defined for this sample and date"},
        )


class VariantProcessingIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.state = core.models.SampleState.objects.create(state="Defined")
        cls.sample = core.models.Sample.objects.create(
            state=cls.state,
            sample_unique_id="RL-VAR-0001",
            sequencing_sample_id="VAR-1",
            collecting_lab_sample_id="COL-VAR-1",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )
        cls.chromosome = core.models.Chromosome.objects.create(chromosome="NC_045512.2")
        cls.gene = core.models.Gene.objects.create(
            chromosomeID=cls.chromosome,
            gene_name="S",
            gene_start=21563,
            gene_end=25384,
        )

    def variant_payload(self):
        return {
            "chromosome": "NC_045512.2",
            "pos": "23063",
            "ref": "A",
            "alt": "T",
            "Filter": "PASS",
            "gene": "S",
            "effect": "missense_variant",
            "dp": "120",
            "ref_dp": "20",
            "alt_dp": "100",
            "af": 0.83,
            "hgvs_c": "c.23063A>T",
            "hgvs_p": "p.N501Y",
            "hgvs_p_1_letter": "N501Y",
        }

    def test_split_variant_data_creates_and_reuses_reference_objects(self):
        cache = core.api.utils.variants.VariantProcessingCache()

        first = core.api.utils.variants.split_variant_data(
            self.variant_payload(),
            self.sample,
            "2026-06-23",
            cache=cache,
        )
        second = core.api.utils.variants.split_variant_data(
            self.variant_payload(),
            self.sample,
            "2026-06-23",
            cache=cache,
        )

        self.assertNotIn("ERROR", first)
        self.assertEqual(
            first["variant_in_sample"]["variantID_id"],
            second["variant_in_sample"]["variantID_id"],
        )
        self.assertEqual(core.models.Variant.objects.count(), 1)
        self.assertEqual(core.models.Filter.objects.count(), 1)
        self.assertEqual(core.models.Effect.objects.count(), 1)
        self.assertEqual(first["variant_ann"]["geneID_id"], str(self.gene.pk))

    def test_variant_annotation_cache_avoids_repeated_database_lookup(self):
        cache = core.api.utils.variants.VariantProcessingCache()
        annotation = {
            "hgvs_c": "c.23063A>T",
            "hgvs_p": "p.N501Y",
            "hgvs_p_1_letter": "N501Y",
        }

        self.assertFalse(
            core.api.utils.variants.variant_annotation_exists(annotation, cache)
        )
        cache.cache_annotation(
            annotation["hgvs_c"],
            annotation["hgvs_p"],
            annotation["hgvs_p_1_letter"],
        )
        with patch(
            "core.api.utils.variants.core.models.VariantAnnotation.objects.filter"
        ) as query:
            self.assertTrue(
                core.api.utils.variants.variant_annotation_exists(annotation, cache)
            )
        query.assert_not_called()

    def test_variant_lookup_reports_unknown_chromosome_and_gene(self):
        missing_chromosome = core.api.utils.variants.get_variant_id(
            {
                **self.variant_payload(),
                "chromosome": "missing",
            }
        )
        missing_gene = core.api.utils.variants.get_required_variant_ann_id(
            {
                **self.variant_payload(),
                "gene": "missing",
            }
        )

        self.assertEqual(
            missing_chromosome["ERROR"],
            core.config.ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE,
        )
        self.assertEqual(
            missing_gene["ERROR"],
            core.config.ERROR_GENE_NOT_DEFINED_IN_DATABASE,
        )


class PublicDatabaseIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="public-db-owner")
        cls.state = core.models.SampleState.objects.create(state="Defined")
        cls.schema = core.models.Schema.objects.create_new_schema(
            {
                "file_name": "schemas/public.json",
                "user_name": cls.user,
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "schema_default": True,
                "schema_app_name": "core",
            }
        )
        cls.sample = core.models.Sample.objects.create(
            state=cls.state,
            sample_unique_id="RL-PUB-0001",
            sequencing_sample_id="PUB-1",
            collecting_lab_sample_id="COL-PUB-1",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )
        cls.database_type = core.models.PublicDatabaseType.objects.create(
            public_type_name="gisaid",
            public_type_display="GISAID",
        )
        cls.field = core.models.PublicDatabaseFields.objects.create(
            database_type=cls.database_type,
            property_name="gisaid_id",
            label_name="GISAID accession",
        )
        cls.field.schemaID.add(cls.schema)

    def test_public_database_storage_persists_matching_schema_fields(self):
        result = core.api.utils.public_db.store_pub_databases_data(
            {"gisaid_id": "EPI_ISL_123"},
            "gisaid",
            self.schema,
            self.sample.pk,
        )

        stored = core.models.PublicDatabaseValues.objects.get()
        self.assertEqual(result, {"SUCCESS": "success"})
        self.assertEqual(stored.sampleID, self.sample)
        self.assertEqual(stored.value, "EPI_ISL_123")


class LaboratoryUtilityTests(TestCase):
    def test_contact_details_and_updates_handle_external_api_results(self):
        user = User.objects.create_user(username="lab-user")
        core.models.Profile.objects.filter(user=user).update(laboratory="Hospital A")

        with patch(
            "core.utils.labs.core.utils.rest_api.get_laboratory_data",
            return_value={"data": {"lab_email": "lab@example.org"}},
        ):
            self.assertEqual(
                core.utils.labs.get_lab_contact_details(user),
                {"lab_email": "lab@example.org"},
            )
        with patch(
            "core.utils.labs.core.utils.rest_api.set_laboratory_data",
            return_value={"SUCCESS": True},
        ) as update:
            self.assertEqual(
                core.utils.labs.update_contact_lab(
                    {"lab_name": "Hospital A", "lab_phone": ""}
                ),
                "OK",
            )
        update.assert_called_once_with({"lab_name": "Hospital A"})

    def test_role_hierarchy_selects_highest_group(self):
        user = User.objects.create_user(username="multi-role")
        user.groups.add(
            Group.objects.create(name="Collector"),
            Group.objects.create(name="RelecovManager"),
        )

        self.assertEqual(
            core.utils.generic_functions.get_user_role(user),
            "RelecovManager",
        )


class AdditionalApiValidationTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(pk=1, is_authenticated=True)

    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_sample_reports_missing_required_identifiers(self, get_schema):
        schema = MagicMock()
        schema.get_schema_id.return_value = "1"
        get_schema.return_value = schema
        request = self.factory.post(
            "/api/createSampleData",
            {
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "sequencing_sample_id": "SEQ-1",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = core.api.views.create_sample_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("collecting_lab_sample_id", response.data["ERROR"])
        self.assertIn("submitting_institution", response.data["ERROR"])

    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_sample_requires_collecting_institution_code(self, get_schema):
        schema = MagicMock()
        schema.get_schema_id.return_value = "1"
        get_schema.return_value = schema
        request = self.factory.post(
            "/api/createSampleData",
            {
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "sequencing_sample_id": "SEQ-1",
                "collecting_lab_sample_id": "COL-1",
                "submitting_institution": "Submitter A",
            },
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = core.api.views.create_sample_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("collecting_institution_code_1", response.data["ERROR"])


class ApiViewBranchCoverageTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(pk=1, is_authenticated=True)

    def post(self, path, data):
        request = self.factory.post(path, data, format="json")
        force_authenticate(request, user=self.user)
        return request

    def put(self, path, data):
        request = self.factory.put(path, data, format="json")
        force_authenticate(request, user=self.user)
        return request

    def schema(self, schema_id=7):
        schema = MagicMock()
        schema.get_schema_id.return_value = schema_id
        return schema

    def sample(self):
        sample = MagicMock()
        sample.sample_unique_id = "RL-API-1"
        sample.sequencing_sample_id = "SEQ-1"
        sample.get_sample_id.return_value = 42
        sample.get_sample_unique_id.return_value = "RL-API-1"
        sample.get_sequencing_sample_id.return_value = "SEQ-1"
        return sample

    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_sample_requires_resolvable_collecting_institution(
        self, get_schema
    ):
        get_schema.return_value = self.schema()
        request = self.post(
            "/api/createSampleData",
            {
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "sequencing_sample_id": "SEQ-1",
                "collecting_lab_sample_id": "COL-1",
                "submitting_institution": "Submitter A",
                "collecting_institution_code_1": "LAB-01",
            },
        )

        with patch(
            "core.api.views.core.utils.lab_catalog.ensure_lab_display",
            return_value="",
        ):
            response = core.api.views.create_sample_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("collecting_institution", response.data["ERROR"])

    @patch(
        "core.api.views.core.api.serializers.CreateSampleSerializer"
    )
    @patch("core.api.views.core.api.utils.samples.split_sample_data")
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_fingerprint",
        return_value=None,
    )
    @patch(
        "core.api.views.core.utils.samples.build_sample_fingerprint",
        return_value="fingerprint",
    )
    @patch(
        "core.api.views.core.utils.lab_catalog.ensure_lab_display",
        return_value="Hospital A",
    )
    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_sample_returns_serializer_validation_errors(
        self,
        get_schema,
        _display,
        _fingerprint,
        _found,
        split_sample,
        serializer_class,
    ):
        get_schema.return_value = self.schema()
        split_sample.return_value = {
            "sample": {"state": 1},
            "ena": {},
            "gisaid": {},
            "author": {},
        }
        serializer = MagicMock()
        serializer.is_valid.return_value = False
        serializer.errors = {"sequencing_sample_id": ["required"]}
        serializer_class.return_value = serializer
        request = self.post(
            "/api/createSampleData",
            {
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "sequencing_sample_id": "SEQ-1",
                "collecting_lab_sample_id": "COL-1",
                "submitting_institution": "Submitter A",
                "collecting_institution_code_1": "LAB-01",
            },
        )

        response = core.api.views.create_sample_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["ERROR"], {"sequencing_sample_id": ["required"]})

    @patch("core.api.views.core.api.utils.public_db.store_pub_databases_data")
    @patch(
        "core.api.views.core.models.SampleState.objects.filter"
    )
    @patch(
        "core.api.views.core.api.serializers.CreateDateAfterChangeStateSerializer"
    )
    @patch(
        "core.api.views.core.api.serializers.CreateSampleSerializer"
    )
    @patch("core.api.views.core.api.utils.samples.split_sample_data")
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_fingerprint",
        return_value=None,
    )
    @patch(
        "core.api.views.core.utils.samples.build_sample_fingerprint",
        return_value="fingerprint",
    )
    @patch(
        "core.api.views.core.utils.lab_catalog.ensure_lab_display",
        return_value="Hospital A",
    )
    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_sample_propagates_ena_storage_error(
        self,
        get_schema,
        _display,
        _fingerprint,
        _found,
        split_sample,
        sample_serializer_class,
        date_serializer_class,
        _state_filter,
        store_public,
    ):
        get_schema.return_value = self.schema()
        sample = self.sample()
        split_sample.return_value = {
            "sample": {"state": 1},
            "ena": {"ena_sample_accession": "ERS1"},
            "gisaid": {},
            "author": {},
        }
        sample_serializer = MagicMock()
        sample_serializer.is_valid.return_value = True
        sample_serializer.save.return_value = sample
        sample_serializer_class.return_value = sample_serializer
        date_serializer = MagicMock()
        date_serializer.is_valid.return_value = True
        date_serializer_class.return_value = date_serializer
        store_public.return_value = {"ERROR": "ENA failed"}
        request = self.post(
            "/api/createSampleData",
            {
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "sequencing_sample_id": "SEQ-1",
                "collecting_lab_sample_id": "COL-1",
                "submitting_institution": "Submitter A",
                "collecting_institution_code_1": "LAB-01",
            },
        )

        response = core.api.views.create_sample_data(request)

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.data["message"], "Error processing ena data")

    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists",
        return_value=None,
    )
    def test_create_bioinfo_metadata_rejects_unknown_schema(self, _schema):
        request = self.post(
            "/api/createBioinfoMetadata",
            {"schema_name": "missing", "schema_version": "0"},
        )

        response = core.api.views.create_bioinfo_metadata(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["ERROR"], "schema name and version is not defined"
        )

    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_bioinfo_metadata_requires_unique_sample_id(self, get_schema):
        get_schema.return_value = self.schema()
        request = self.post(
            "/api/createBioinfoMetadata",
            {"schema_name": "RELECOV", "schema_version": "1.0"},
        )

        response = core.api.views.create_bioinfo_metadata(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["ERROR"], core.config.ERROR_SAMPLE_NAME_NOT_INCLUDED)

    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_unique_sample_id",
        return_value=None,
    )
    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_bioinfo_metadata_rejects_unknown_sample(
        self, get_schema, _sample
    ):
        get_schema.return_value = self.schema()
        request = self.post(
            "/api/createBioinfoMetadata",
            {
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "unique_sample_id": "RL-MISSING",
            },
        )

        response = core.api.views.create_bioinfo_metadata(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["ERROR"], core.config.ERROR_SAMPLE_NOT_DEFINED)

    @patch(
        "core.api.views.core.api.utils.bioinfo_metadata.get_analysis_defined",
        return_value=["2024-01-01"],
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_unique_sample_id"
    )
    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_bioinfo_metadata_rejects_duplicate_analysis_date(
        self, get_schema, get_sample, _defined
    ):
        get_schema.return_value = self.schema()
        get_sample.return_value = self.sample()
        request = self.post(
            "/api/createBioinfoMetadata",
            {
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "unique_sample_id": "RL-API-1",
                "bioinformatics_analysis_date": "2024-01-01",
            },
        )

        response = core.api.views.create_bioinfo_metadata(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["ERROR"], core.config.ERROR_ANALYSIS_ALREADY_DEFINED
        )

    @patch(
        "core.api.views.core.api.utils.bioinfo_metadata.split_bioinfo_data",
        return_value={"ERROR": "split failed"},
    )
    @patch(
        "core.api.views.core.api.utils.bioinfo_metadata.get_analysis_defined",
        return_value=[],
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_unique_sample_id"
    )
    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_bioinfo_metadata_propagates_split_errors(
        self, get_schema, get_sample, _defined, _split
    ):
        get_schema.return_value = self.schema()
        get_sample.return_value = self.sample()
        request = self.post(
            "/api/createBioinfoMetadata",
            {"unique_sample_id": "RL-API-1"},
        )

        response = core.api.views.create_bioinfo_metadata(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["ERROR"], "split failed")

    @patch(
        "core.api.views.core.api.utils.bioinfo_metadata.store_bioinfo_data",
        return_value={"ERROR": "store failed"},
    )
    @patch(
        "core.api.views.core.api.utils.bioinfo_metadata.split_bioinfo_data",
        return_value={"analysis": {"value": 1}},
    )
    @patch(
        "core.api.views.core.api.utils.bioinfo_metadata.get_analysis_defined",
        return_value=[],
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_unique_sample_id"
    )
    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_bioinfo_metadata_propagates_store_errors(
        self, get_schema, get_sample, _defined, _split, _store
    ):
        get_schema.return_value = self.schema()
        get_sample.return_value = self.sample()
        request = self.post(
            "/api/createBioinfoMetadata",
            {"unique_sample_id": "RL-API-1"},
        )

        response = core.api.views.create_bioinfo_metadata(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["ERROR"], "store failed")

    @patch(
        "core.api.views.core.api.serializers.CreateDateAfterChangeStateSerializer"
    )
    @patch("core.api.views.core.models.SampleState.objects.filter")
    @patch(
        "core.api.views.core.api.utils.bioinfo_metadata.store_bioinfo_data",
        return_value={"SUCCESS": "stored"},
    )
    @patch(
        "core.api.views.core.api.utils.bioinfo_metadata.split_bioinfo_data",
        return_value={"analysis": {"value": 1}},
    )
    @patch(
        "core.api.views.core.api.utils.bioinfo_metadata.get_analysis_defined",
        return_value=[],
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_unique_sample_id"
    )
    @patch(
        "core.api.views.core.api.utils.common_functions.get_schema_version_if_exists"
    )
    def test_create_bioinfo_metadata_success_updates_state_and_date(
        self,
        get_schema,
        get_sample,
        _defined,
        _split,
        _store,
        state_filter,
        date_serializer_class,
    ):
        sample = self.sample()
        get_schema.return_value = self.schema()
        get_sample.return_value = sample
        state_filter.return_value.last.return_value.get_state_id.return_value = 3
        date_serializer = MagicMock()
        date_serializer.is_valid.return_value = True
        date_serializer_class.return_value = date_serializer
        request = self.post(
            "/api/createBioinfoMetadata",
            {
                "unique_sample_id": "RL-API-1",
                "bioinformatics_analysis_date": "2024-01-01",
            },
        )

        response = core.api.views.create_bioinfo_metadata(request)

        self.assertEqual(response.status_code, 201)
        sample.update_state.assert_called_once_with("Bioinfo")
        date_serializer.save.assert_called_once_with()
        self.assertEqual(response.data["data"]["state"], "Bioinfo")

    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_unique_sample_id",
        return_value=None,
    )
    def test_create_variant_data_rejects_unknown_unique_sample_id(self, _sample):
        request = self.post(
            "/api/createVariantData",
            {
                "unique_sample_id": "RL-MISSING",
                "sample_name": "SEQ-1",
                "bioinformatics_analysis_date": "2024-01-01",
            },
        )

        response = core.api.views.create_variant_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("unique_sample_id", response.data["message"])

    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_unique_sample_id",
        return_value=None,
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_sample_name",
        return_value=None,
    )
    def test_create_variant_data_rejects_missing_sample_identifier(
        self, _sample_name, _unique
    ):
        request = self.post(
            "/api/createVariantData",
            {
                "sample_name": "missing",
                "bioinformatics_analysis_date": "2024-01-01",
            },
        )

        response = core.api.views.create_variant_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "Sample identifier not found in platform")

    @patch("core.api.views.core.api.utils.variants.get_variant_analysis_defined")
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_unique_sample_id"
    )
    def test_create_variant_data_rejects_mismatched_identifiers(
        self, get_unique, _defined
    ):
        sample = self.sample()
        sample.sample_unique_id = "RL-API-1"
        sample.sequencing_sample_id = "SEQ-1"
        get_unique.return_value = sample
        request = self.post(
            "/api/createVariantData",
            {
                "unique_sample_id": "RL-API-1",
                "sample_name": "OTHER",
                "bioinformatics_analysis_date": "2024-01-01",
            },
        )

        response = core.api.views.create_variant_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("does not match", response.data["message"])

    @patch(
        "core.api.views.core.api.utils.variants.get_variant_analysis_defined",
        return_value=["2024-01-01"],
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_sample_name"
    )
    def test_create_variant_data_rejects_duplicate_analysis_date(
        self, get_sample, _defined
    ):
        get_sample.return_value = self.sample()
        request = self.post(
            "/api/createVariantData",
            {
                "sample_name": "SEQ-1",
                "bioinformatics_analysis_date": "2024-01-01",
            },
        )

        response = core.api.views.create_variant_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["ERROR"], core.config.ERROR_ANALYSIS_ALREADY_DEFINED
        )

    @patch(
        "core.api.views.core.api.utils.variants.get_variant_analysis_defined",
        return_value=[],
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_sample_name"
    )
    def test_create_variant_data_requires_variants_key(self, get_sample, _defined):
        get_sample.return_value = self.sample()
        request = self.post(
            "/api/createVariantData",
            {
                "sample_name": "SEQ-1",
                "bioinformatics_analysis_date": "2024-01-01",
            },
        )

        response = core.api.views.create_variant_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["ERROR"], core.config.ERROR_VARIANT_INFORMATION_NOT_DEFINED
        )

    @patch(
        "core.api.views.core.api.utils.variants.get_variant_analysis_defined",
        return_value=[],
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_sample_name"
    )
    def test_create_variant_data_reports_unparseable_variant_string(
        self, get_sample, _defined
    ):
        get_sample.return_value = self.sample()
        request = self.post(
            "/api/createVariantData",
            {
                "sample_name": "SEQ-1",
                "bioinformatics_analysis_date": "2024-01-01",
                "variants": "[",
            },
        )

        response = core.api.views.create_variant_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unable to parse variants", response.data["ERROR"])

    @patch(
        "core.api.views.core.api.utils.variants.split_variant_data",
        return_value={"ERROR": "bad variant"},
    )
    @patch(
        "core.api.views.core.api.utils.variants.get_variant_analysis_defined",
        return_value=[],
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_sample_name"
    )
    def test_create_variant_data_propagates_split_errors(
        self, get_sample, _defined, _split
    ):
        get_sample.return_value = self.sample()
        request = self.post(
            "/api/createVariantData",
            {
                "sample_name": "SEQ-1",
                "bioinformatics_analysis_date": "2024-01-01",
                "variants": [{}],
            },
        )

        response = core.api.views.create_variant_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["ERROR"], {"ERROR": "bad variant"})

    @patch(
        "core.api.views.core.api.utils.variants.split_variant_data",
        return_value={
            "variant_in_sample": {"variantID_id": "bad"},
            "variant_ann": {},
        },
    )
    @patch(
        "core.api.views.core.api.utils.variants.get_variant_analysis_defined",
        return_value=[],
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_sample_name"
    )
    def test_create_variant_data_rejects_invalid_variant_id(
        self, get_sample, _defined, _split
    ):
        get_sample.return_value = self.sample()
        request = self.post(
            "/api/createVariantData",
            {
                "sample_name": "SEQ-1",
                "bioinformatics_analysis_date": "2024-01-01",
                "variants": [{}],
            },
        )

        response = core.api.views.create_variant_data(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid variantID_id", response.data["ERROR"])

    @patch("core.api.views.core.api.utils.common_functions.update_change_state_date")
    @patch("core.api.views.transaction.atomic")
    @patch("core.api.views.core.models.SampleState.objects.filter")
    @patch("core.api.views.core.models.VariantAnnotation")
    @patch("core.api.views.core.models.VariantInSample")
    @patch(
        "core.api.views.core.api.utils.variants.variant_annotation_exists",
        side_effect=[False, False],
    )
    @patch(
        "core.api.views.core.api.utils.variants.split_variant_data"
    )
    @patch(
        "core.api.views.core.api.utils.variants.get_variant_analysis_defined",
        return_value=[],
    )
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_sample_name"
    )
    def test_create_variant_data_success_flushes_deduplicated_annotations(
        self,
        get_sample,
        _defined,
        split_variant,
        _annotation_exists,
        variant_model,
        annotation_model,
        state_filter,
        _atomic,
        update_date,
    ):
        sample = self.sample()
        get_sample.return_value = sample
        split_variant.side_effect = [
            {
                "variant_in_sample": {"variantID_id": "10", "af": "0.8"},
                "variant_ann": {
                    "variantID_id": "10",
                    "geneID_id": 1,
                    "effectID_id": 2,
                    "hgvs_c": "c.1A>T",
                    "hgvs_p": "p.K1N",
                    "hgvs_p_1_letter": "K1N",
                },
            },
            {
                "variant_in_sample": {"variantID_id": "10", "af": "0.7"},
                "variant_ann": {
                    "variantID_id": "10",
                    "geneID_id": 1,
                    "effectID_id": 2,
                    "hgvs_c": "c.1A>T",
                    "hgvs_p": "p.K1N",
                    "hgvs_p_1_letter": "K1N",
                },
            },
        ]
        bulk_created_variants = []
        bulk_created_annotations = []

        def capture_bulk_created_variants(objects, **kwargs):
            bulk_created_variants.append((list(objects), kwargs))

        def capture_bulk_created_annotations(objects, **kwargs):
            bulk_created_annotations.append((list(objects), kwargs))

        variant_model.objects.bulk_create = MagicMock(
            side_effect=capture_bulk_created_variants
        )
        annotation_model.objects.bulk_create = MagicMock(
            side_effect=capture_bulk_created_annotations
        )
        variant_model.side_effect = ["variant-obj-1", "variant-obj-2"]
        annotation_model.return_value = "annotation-obj"
        state_filter.return_value.last.return_value.get_state_id.return_value = 5
        request = self.post(
            "/api/createVariantData",
            {
                "sample_name": "SEQ-1",
                "bioinformatics_analysis_date": "2024-01-01",
                "variants": [{}, {}],
            },
        )

        response = core.api.views.create_variant_data(request)

        self.assertEqual(response.status_code, 201)
        variant_model.objects.bulk_create.assert_called_once()
        annotation_model.objects.bulk_create.assert_called_once()
        self.assertEqual(
            bulk_created_variants,
            [(["variant-obj-1", "variant-obj-2"], {"batch_size": 250})],
        )
        self.assertEqual(
            bulk_created_annotations,
            [(["annotation-obj"], {"batch_size": 250})],
        )
        sample.update_state.assert_called_once_with("Variant")
        update_date.assert_called_once_with(42, 5)

    @patch(
        "core.api.views.core.api.serializers.UpdateStateSampleSerializer"
    )
    @patch("core.api.views.core.models.SampleState.objects.filter")
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_sample_name"
    )
    def test_update_state_returns_serializer_validation_error(
        self, get_sample, state_filter, serializer_class
    ):
        get_sample.return_value = self.sample()
        state_query = MagicMock()
        state_query.exists.return_value = True
        state_query.last.return_value.get_state_id.return_value = 2
        state_filter.return_value = state_query
        serializer = MagicMock()
        serializer.is_valid.return_value = False
        serializer.errors = {"state": ["invalid"]}
        serializer_class.return_value = serializer
        request = self.put(
            "/api/updateState",
            {"sample_name": "SEQ-1", "state": "Bioinfo"},
        )

        response = core.api.views.update_state(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["ERROR"], {"state": ["invalid"]})

    @patch("core.api.views.core.api.utils.common_functions.update_change_state_date")
    @patch(
        "core.api.views.core.api.serializers.CreateErrorSerializer"
    )
    @patch("core.api.views.core.models.Error.objects.filter")
    @patch(
        "core.api.views.core.api.serializers.UpdateStateSampleSerializer"
    )
    @patch("core.api.views.core.models.SampleState.objects.filter")
    @patch(
        "core.api.views.core.utils.samples.get_sample_obj_from_sample_name"
    )
    def test_update_state_error_state_validates_error_serializer(
        self,
        get_sample,
        state_filter,
        state_serializer_class,
        error_filter,
        error_serializer_class,
        _update_date,
    ):
        get_sample.return_value = self.sample()
        state_query = MagicMock()
        state_query.exists.return_value = True
        state_query.last.return_value.get_state_id.return_value = 9
        state_filter.return_value = state_query
        state_serializer = MagicMock()
        state_serializer.is_valid.return_value = True
        state_serializer_class.return_value = state_serializer
        error_filter.return_value.last.return_value.get_error_id.return_value = 4
        error_serializer = MagicMock()
        error_serializer.is_valid.return_value = False
        error_serializer.errors = {"error_type": ["invalid"]}
        error_serializer_class.return_value = error_serializer
        request = self.put(
            "/api/updateState",
            {
                "sample_name": "SEQ-1",
                "state": "Error",
                "error_type": "Contamination",
            },
        )

        response = core.api.views.update_state(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["ERROR"], {"error_type": ["invalid"]})


class ApiCommonFunctionIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="api-common-owner")
        cls.state = core.models.SampleState.objects.create(state="Defined")
        cls.schema = core.models.Schema.objects.create_new_schema(
            {
                "file_name": "schemas/api-common.json",
                "user_name": cls.user,
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "schema_default": True,
                "schema_app_name": "core",
            }
        )
        cls.sample = core.models.Sample.objects.create(
            state=cls.state,
            sample_unique_id="RL-COMMON-1",
            sequencing_sample_id="COMMON-1",
            collecting_lab_sample_id="COL-COMMON-1",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )

    def test_schema_lookup_matches_name_version_and_application(self):
        found = core.api.utils.common_functions.get_schema_version_if_exists(
            {"schema_name": "relecov", "schema_version": "1.0"}
        )
        missing = core.api.utils.common_functions.get_schema_version_if_exists(
            {"schema_name": "RELECOV", "schema_version": "2.0"}
        )

        self.assertEqual(found, self.schema)
        self.assertIsNone(missing)

    def test_state_change_date_is_recorded(self):
        core.api.utils.common_functions.update_change_state_date(
            self.sample.pk,
            self.state.pk,
        )

        change = core.models.DateUpdateState.objects.get()
        self.assertEqual(change.sampleID, self.sample)
        self.assertEqual(change.stateID, self.state)


class SampleApiBranchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.defined = core.models.SampleState.objects.create(state="Defined")

    def test_prepare_fields_reports_missing_initial_state(self):
        core.models.SampleState.objects.all().delete()

        result = core.api.utils.samples.prepare_fields_in_sample({"value": "x"})

        self.assertEqual(
            result,
            {"ERROR": core.config.ERROR_INTIAL_SETTINGS_NOT_DEFINED},
        )

    def test_prepare_fields_adds_state_and_optional_public_fields(self):
        result = core.api.utils.samples.prepare_fields_in_sample({"value": "x"})

        self.assertEqual(result["state"], str(self.defined.pk))
        self.assertIsNone(result["biosample_accession_ENA"])
        self.assertIsNone(result["virus_name"])
        self.assertIsNone(result["gisaid_id"])

    @patch(
        "core.api.utils.samples.core.utils.samples.get_user_id_from_submitting_institution",
        return_value=None,
    )
    def test_split_sample_data_preserves_requested_id_and_nulls_invalid_date(
        self,
        _get_user,
    ):
        result = core.api.utils.samples.split_sample_data(
            {
                "unique_sample_id": "CUSTOM-ID",
                "submitting_institution": "Submitter A",
                "sequencing_date": "invalid",
            }
        )

        self.assertEqual(result["sample"]["sample_unique_id"], "CUSTOM-ID")
        self.assertIsNone(result["sample"]["sequencing_date"])

    @patch(
        "core.api.utils.samples.core.utils.samples.get_user_id_from_submitting_institution",
        return_value=None,
    )
    def test_split_sample_data_increments_last_generated_id(self, _get_user):
        core.models.Sample.objects.create(
            state=self.defined,
            sample_unique_id="RL-AAA-0001",
            sequencing_sample_id="SEQ-OLD",
            collecting_lab_sample_id="COL-OLD",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )

        result = core.api.utils.samples.split_sample_data(
            {"submitting_institution": "Submitter A"}
        )

        self.assertEqual(result["sample"]["sample_unique_id"], "RL-AAA-0002")


class ApiEndpointIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="api-endpoint-user")
        cls.defined = core.models.SampleState.objects.create(state="Defined")
        cls.bioinfo = core.models.SampleState.objects.create(state="Bioinfo")
        cls.sample = core.models.Sample.objects.create(
            state=cls.defined,
            sample_unique_id="RL-ENDPOINT-1",
            sequencing_sample_id="ENDPOINT-1",
            collecting_lab_sample_id="COL-ENDPOINT-1",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_check_sample_exists_returns_serialized_sample(self):
        request = self.factory.get(
            "/api/checkSampleExists",
            {
                "sequencing_sample_id": self.sample.sequencing_sample_id,
                "collecting_lab_sample_id": self.sample.collecting_lab_sample_id,
                "submitting_institution": self.sample.submitting_institution,
                "collecting_institution": self.sample.collecting_institution,
            },
        )
        force_authenticate(request, user=self.user)

        response = core.api.views.check_sample_exists(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Sample found")
        self.assertEqual(
            response.data["data"]["sequencing_sample_id"],
            self.sample.sequencing_sample_id,
        )

    def test_update_state_changes_sample_and_records_date(self):
        request = self.factory.put(
            "/api/updateState",
            {"sample_name": self.sample.sequencing_sample_id, "state": "Bioinfo"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = core.api.views.update_state(request)

        self.sample.refresh_from_db()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.sample.state, self.bioinfo)
        self.assertTrue(
            core.models.DateUpdateState.objects.filter(
                sampleID=self.sample,
                stateID=self.bioinfo,
            ).exists()
        )

    def test_update_state_rejects_unknown_state(self):
        request = self.factory.put(
            "/api/updateState",
            {"sample_name": self.sample.sequencing_sample_id, "state": "Unknown"},
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = core.api.views.update_state(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn("does not exist", response.data["ERROR"])


class AdditionalSearchSampleBranchTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = SimpleNamespace(is_authenticated=True)

    @patch("core.views._get_search_sample_rows_for_user")
    def test_search_endpoint_returns_upstream_error_payload(self, get_rows):
        get_rows.return_value = {"ERROR": "No samples available"}
        request = self.factory.get("/searchSample/data", {"draw": "invalid"})
        request.user = self.user

        response = search_sample_data(request)
        payload = json.loads(response.content)

        self.assertEqual(payload["recordsTotal"], 0)
        self.assertEqual(payload["data"], [])
        self.assertEqual(payload["error"], "No samples available")

    @patch("core.views._get_search_sample_rows_for_user")
    def test_search_endpoint_supports_global_search_and_unlimited_length(
        self,
        get_rows,
    ):
        get_rows.return_value = [
            {
                "id": 1,
                "sequencing_id": "SEQ-001",
                "collection_date": "2026-01-01",
                "lineage": "XFG.3",
                "collecting_institution": "Hospital A",
            },
            {
                "id": 2,
                "sequencing_id": "SEQ-002",
                "collection_date": "2026-01-02",
                "lineage": "JN.1",
                "collecting_institution": "Hospital B",
            },
        ]
        request = self.factory.get(
            "/searchSample/data",
            {
                "start": "0",
                "length": "-1",
                "search[value]": "hospital",
                "search[regex]": "false",
                "columns[0][search][value]": "SEQ-00",
                "columns[0][search][regex]": "false",
                "order[0][column]": "invalid",
                "order[0][dir]": "desc",
            },
        )
        request.user = self.user

        response = search_sample_data(request)
        payload = json.loads(response.content)

        self.assertEqual(payload["recordsFiltered"], 2)
        self.assertEqual(
            [row["sequencing_id"] for row in payload["data"]],
            ["SEQ-002", "SEQ-001"],
        )

    def test_row_matching_rejects_global_and_column_mismatches(self):
        row = {
            "sequencing_id": "SEQ-001",
            "collection_date": "2026-01-01",
            "lineage": "XFG.3",
            "collecting_institution": "Hospital A",
        }

        self.assertFalse(_row_matches_search(row, "missing", []))
        self.assertFalse(
            _row_matches_search(
                row,
                "",
                [("lineage", "JN.1", True)],
            )
        )
        self.assertFalse(
            _row_matches_search(
                row,
                "",
                [("sequencing_id", "XYZ", False)],
            )
        )


class LineageDetailIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="lineage-detail-owner")
        cls.state = core.models.SampleState.objects.create(state="Defined")
        cls.schema = core.models.Schema.objects.create_new_schema(
            {
                "file_name": "schemas/lineage.json",
                "user_name": cls.user,
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "schema_default": True,
                "schema_app_name": "core",
            }
        )
        cls.sample = core.models.Sample.objects.create(
            state=cls.state,
            schema_obj=cls.schema,
            sample_unique_id="RL-LINEAGE-1",
            sequencing_sample_id="LINEAGE-1",
            collecting_lab_sample_id="COL-LINEAGE-1",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )

    def test_lineage_details_return_none_without_sample_or_schema_fields(self):
        self.assertIsNone(core.utils.lineage.get_lineage_data_from_sample(999999))
        self.assertIsNone(
            core.utils.lineage.get_lineage_data_from_sample(self.sample.pk)
        )

    def test_lineage_details_include_present_and_missing_values(self):
        assignment = core.models.LineageFields.objects.create(
            property_name="lineage_assignment",
            label_name="Lineage",
        )
        clade = core.models.LineageFields.objects.create(
            property_name="clade",
            label_name="Clade",
        )
        assignment.schemaID.add(self.schema)
        clade.schemaID.add(self.schema)
        value = core.models.LineageValues.objects.create(
            lineage_fieldID=assignment,
            value="XFG.3",
        )
        self.sample.lineage_values.add(value)

        result = core.utils.lineage.get_lineage_data_from_sample(self.sample.pk)

        self.assertCountEqual(
            result,
            [["Lineage", "XFG.3"], ["Clade", ""]],
        )


class SampleSearchIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="sample-search-manager")
        cls.user.groups.add(Group.objects.create(name="RelecovManager"))
        cls.defined = core.models.SampleState.objects.create(state="Defined")
        cls.bioinfo = core.models.SampleState.objects.create(state="Bioinfo")
        cls.first = core.models.Sample.objects.create(
            state=cls.defined,
            sample_unique_id="RL-SEARCH-1",
            sequencing_sample_id="SEARCH-001",
            collecting_lab_sample_id="COL-001",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )
        cls.second = core.models.Sample.objects.create(
            state=cls.defined,
            sample_unique_id="RL-SEARCH-2",
            sequencing_sample_id="SEARCH-002",
            collecting_lab_sample_id="COL-002",
            submitting_institution="Submitter B",
            collecting_institution="Hospital B",
        )
        core.models.DateUpdateState.objects.create(
            sampleID=cls.first,
            stateID=cls.bioinfo,
        )

    def test_exact_and_partial_sample_search_return_single_identifier(self):
        exact = core.utils.samples.search_samples(
            "SEARCH-001",
            "",
            "",
            "",
            self.user,
        )
        partial = core.utils.samples.search_samples(
            "002",
            "",
            "",
            "",
            self.user,
        )

        self.assertEqual(exact, [str(self.first.pk)])
        self.assertEqual(partial, [str(self.second.pk)])

    def test_sample_search_returns_empty_for_unknown_name(self):
        self.assertEqual(
            core.utils.samples.search_samples(
                "UNKNOWN",
                "",
                "",
                "",
                self.user,
            ),
            [],
        )

    def test_sample_search_combines_lab_and_state_filters(self):
        result = core.utils.samples.search_samples(
            "",
            "Hospital A",
            str(self.bioinfo.pk),
            "",
            self.user,
        )

        self.assertEqual(result, [str(self.first.pk)])

    def test_unfiltered_sample_search_returns_summary_rows(self):
        result = core.utils.samples.search_samples("", "", "", "", self.user)

        self.assertEqual(len(result), 2)
        self.assertCountEqual([row[1] for row in result], ["SEARCH-001", "SEARCH-002"])

    def test_received_sample_counts_support_daily_and_accumulated_modes(self):
        daily = core.utils.samples.get_all_recieved_samples_with_dates()
        accumulated = core.utils.samples.get_all_recieved_samples_with_dates(
            accumulated=True
        )

        self.assertEqual(sum(next(iter(item.values())) for item in daily), 2)
        self.assertEqual(next(iter(accumulated[-1].values())), 2)


class PublicDatabaseQueryIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.state = core.models.SampleState.objects.create(state="Defined")
        cls.sample = core.models.Sample.objects.create(
            state=cls.state,
            sample_unique_id="RL-PUBLIC-QUERY-1",
            sequencing_sample_id="PUBLIC-QUERY-1",
            collecting_lab_sample_id="COL-PUBLIC-QUERY-1",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )
        db_type = core.models.PublicDatabaseType.objects.create(
            public_type_name="gisaid",
            public_type_display="GISAID",
        )
        cls.field = core.models.PublicDatabaseFields.objects.create(
            database_type=db_type,
            property_name="gisaid_id",
            label_name="GISAID accession",
        )
        core.models.PublicDatabaseValues.objects.create(
            public_database_fieldID=cls.field,
            sampleID=cls.sample,
            value="EPI_ISL_123",
        )
        core.models.PublicDatabaseValues.objects.create(
            public_database_fieldID=cls.field,
            sampleID=cls.sample,
            value="Not Provided",
        )

    def test_accession_queries_exclude_empty_values_for_global_and_scoped_modes(self):
        global_values = list(
            core.utils.public_db.get_public_accession_from_sample_lab("gisaid_id")
        )
        scoped_values = list(
            core.utils.public_db.get_public_accession_from_sample_lab(
                "gisaid_id",
                [self.sample],
            )
        )

        self.assertEqual(len(global_values), 1)
        self.assertEqual(global_values[0][2], "EPI_ISL_123")
        self.assertEqual(scoped_values, [(self.sample.sample_fingerprint, "EPI_ISL_123")])

    def test_public_information_returns_values_or_empty_list(self):
        self.assertEqual(
            list(
                core.utils.public_db.get_public_information_from_sample(
                    "gisaid",
                    self.sample.pk,
                )
            ),
            [
                ("GISAID accession", "EPI_ISL_123"),
                ("GISAID accession", "Not Provided"),
            ],
        )
        self.assertEqual(
            core.utils.public_db.get_public_information_from_sample(
                "ena",
                self.sample.pk,
            ),
            [],
        )

    @patch(
        "core.utils.public_db.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value={"uploaded": 3},
    )
    def test_preprocessed_public_data_uses_cached_payload(self, _cached):
        self.assertEqual(
            core.utils.public_db.get_preprocessed_gisaid_data(),
            {"uploaded": 3},
        )
        self.assertEqual(
            core.utils.public_db.get_preprocessed_ena_data(),
            {"uploaded": 3},
        )

    @patch(
        "core.utils.public_db.dashboard.utils.generic_process_data.pre_proc_intranet_gisaid_data",
        return_value={"ERROR": "Unable to preprocess"},
    )
    @patch(
        "core.utils.public_db.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value=None,
    )
    def test_preprocessed_public_data_propagates_processing_error(
        self,
        _cached,
        _preprocess,
    ):
        self.assertEqual(
            core.utils.public_db.get_preprocessed_gisaid_data(),
            {"ERROR": "Unable to preprocess"},
        )


class BioinfoAnalysisUtilityIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="bioinfo-util-owner")
        cls.defined = core.models.SampleState.objects.create(state="Defined")
        cls.bioinfo = core.models.SampleState.objects.create(state="Bioinfo")
        cls.schema = core.models.Schema.objects.create_new_schema(
            {
                "file_name": "schemas/bioinfo-util.json",
                "user_name": cls.user,
                "schema_name": "RELECOV",
                "schema_version": "1.0",
                "schema_default": True,
                "schema_app_name": "core",
            }
        )
        cls.sample_with_value = core.models.Sample.objects.create(
            state=cls.defined,
            schema_obj=cls.schema,
            sample_unique_id="RL-BIOUTIL-1",
            sequencing_sample_id="BIOUTIL-1",
            collecting_lab_sample_id="COL-BIOUTIL-1",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )
        cls.sample_without_value = core.models.Sample.objects.create(
            state=cls.defined,
            schema_obj=cls.schema,
            sample_unique_id="RL-BIOUTIL-2",
            sequencing_sample_id="BIOUTIL-2",
            collecting_lab_sample_id="COL-BIOUTIL-2",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )
        cls.depth_field = core.models.BioinfoAnalysisField.objects.create(
            property_name="depth",
            label_name="Depth",
        )
        cls.empty_field = core.models.BioinfoAnalysisField.objects.create(
            property_name="empty_field",
            label_name="Empty field",
        )
        cls.never_used_field = core.models.BioinfoAnalysisField.objects.create(
            property_name="never_used",
            label_name="Never used",
        )
        cls.depth_field.schemaID.add(cls.schema)
        cls.empty_field.schemaID.add(cls.schema)
        cls.never_used_field.schemaID.add(cls.schema)
        depth_value = core.models.BioinfoAnalysisValue.objects.create(
            value="1500",
            bioinfo_analysis_fieldID=cls.depth_field,
        )
        empty_value = core.models.BioinfoAnalysisValue.objects.create(
            value="Not Provided",
            bioinfo_analysis_fieldID=cls.empty_field,
        )
        cls.sample_with_value.bio_analysis_values.add(depth_value, empty_value)
        core.models.DateUpdateState.objects.create(
            sampleID=cls.sample_with_value,
            stateID=cls.bioinfo,
        )

    def test_bio_analysis_stats_cover_global_and_laboratory_modes(self):
        self.assertEqual(
            core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab(),
            {"analized": 1, "received": 2},
        )
        self.assertEqual(
            core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab(
                "Submitter A"
            ),
            {"analized": 1, "received": 2},
        )

    def test_bioinfo_sample_details_include_present_and_missing_values(self):
        result = core.utils.bioinfo_analysis.get_bioinfo_analysis_data_from_sample(
            self.sample_with_value.pk
        )

        self.assertCountEqual(
            result,
            [
                ["Depth", "1500"],
                ["Empty field", "Not Provided"],
                ["Never used", ""],
            ],
        )
        self.assertIsNone(
            core.utils.bioinfo_analysis.get_bioinfo_analysis_data_from_sample(999999)
        )

    def test_bioinfo_utilization_classifies_filled_empty_and_unused_fields(self):
        result = (
            core.utils.bioinfo_analysis.get_bioinfo_analysis_fields_utilization(
                self.schema,
                use_cache=False,
            )
        )

        self.assertEqual(result["fields_value"]["Depth"], 1)
        self.assertEqual(result["fields_value"]["Empty field"], 0)
        self.assertEqual(result["fields_value"]["Never used"], 0)
        self.assertEqual(result["fields_norm"]["Depth"], 0.5)
        self.assertEqual(result["always_none"], ["Empty field"])
        self.assertEqual(result["never_used"], ["Never used"])
        self.assertEqual(result["num_samples"], 2)

    def test_bioinfo_utilization_returns_empty_without_schema_or_samples(self):
        self.assertEqual(
            core.utils.bioinfo_analysis.get_bioinfo_analysis_fields_utilization(
                [],
                use_cache=False,
            ),
            {},
        )
        empty_schema = core.models.Schema.objects.create_new_schema(
            {
                "file_name": "schemas/empty.json",
                "user_name": self.user,
                "schema_name": "EMPTY",
                "schema_version": "1.0",
                "schema_default": False,
                "schema_app_name": "core",
            }
        )
        self.assertEqual(
            core.utils.bioinfo_analysis.get_bioinfo_analysis_fields_utilization(
                empty_schema,
                use_cache=False,
            ),
            {},
        )


class AnnotationUtilityIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="annotation-owner")

    def parsed_annotation(self):
        return {
            "gff_version": "3",
            "gff_spec_version": "1.21",
            "sequence_region": "1_29903",
            "organism_code": "NC_045512",
            "organism_code_version": "2",
            "genes": [
                {"gene_name": "S", "gene_start": "21563", "gene_end": "25384"},
                {"gene_name": "N", "gene_start": "28274", "gene_end": "29533"},
            ],
        }

    def test_store_and_query_annotation_with_ordered_genes(self):
        core.utils.annotation.store_gff(self.parsed_annotation(), self.user)
        annotation = core.models.OrganismAnnotation.objects.get()

        self.assertTrue(core.utils.annotation.check_if_annotation_exists(annotation.pk))
        self.assertTrue(
            core.utils.annotation.check_if_organism_version_exists(
                "NC_045512",
                "2",
            )
        )
        self.assertFalse(core.utils.annotation.check_if_annotation_exists(999999))
        self.assertEqual(len(core.utils.annotation.get_annotations()), 1)
        self.assertEqual(
            core.utils.annotation.get_annotation_data(annotation.pk)["genes"],
            [["S", "21563", "25384"], ["N", "28274", "29533"]],
        )

    def test_store_gff_reuses_existing_chromosome(self):
        core.models.Chromosome.objects.create(chromosome="NC_045512.2")

        core.utils.annotation.store_gff(self.parsed_annotation(), self.user)

        self.assertEqual(core.models.Chromosome.objects.count(), 1)
        self.assertEqual(core.models.Gene.objects.count(), 2)

    @patch(
        "core.utils.annotation.check_if_organism_version_exists",
        return_value=False,
    )
    def test_read_gff_extracts_header_and_gene_rows(self, _exists):
        gff = (
            "##gff-version 3\n"
            "##gff-spec-version 1.21\n"
            "# header\n"
            "# header\n"
            "# header\n"
            "##sequence-region NC_045512.2 1 29903\n"
            "NC_045512.2\tRefSeq\tgene\t21563\t25384\t.\t+\t.\tID=gene-S;gene=S;Name=S\n"
            "NC_045512.2\tRefSeq\tCDS\t21563\t25384\t.\t+\t.\tID=cds-S\n"
        )
        uploaded = MagicMock()
        uploaded.chunks.return_value = [gff.encode("utf-8")]

        result = core.utils.annotation.read_gff_file(uploaded)

        self.assertEqual(result["organism_code"], "NC_045512")
        self.assertEqual(result["organism_code_version"], "2")
        self.assertEqual(result["genes"][0]["gene_name"], "S")

    @patch(
        "core.utils.annotation.check_if_organism_version_exists",
        return_value=True,
    )
    def test_read_gff_rejects_existing_organism_version(self, _exists):
        gff = (
            "##gff-version 3\n"
            "##gff-spec-version 1.21\n"
            "# header\n"
            "# header\n"
            "# header\n"
            "##sequence-region NC_045512.2 1 29903\n"
        )
        uploaded = MagicMock()
        uploaded.chunks.return_value = [gff.encode("utf-8")]

        self.assertEqual(
            core.utils.annotation.read_gff_file(uploaded),
            {"ERROR": core.config.ERROR_ANNOTATION_ORGANISM_ALREADY_EXISTS},
        )


class VariantQueryUtilityIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="variant-query-owner")
        cls.state = core.models.SampleState.objects.create(state="Defined")
        cls.sample = core.models.Sample.objects.create(
            state=cls.state,
            sample_unique_id="RL-VQUERY-1",
            sequencing_sample_id="VQUERY-1",
            collecting_lab_sample_id="COL-VQUERY-1",
            submitting_institution="Submitter A",
            collecting_institution="Hospital A",
        )
        cls.chromosome = core.models.Chromosome.objects.create(
            chromosome="NC_045512.2"
        )
        cls.annotation = core.models.OrganismAnnotation.objects.create(
            user=cls.user,
            chromosomeID=cls.chromosome,
            gff_version="3",
            gff_spec_version="1.21",
            sequence_region="1_29903",
            organism_code="NC_045512",
            organism_code_version="2",
        )
        cls.gene = core.models.Gene.objects.create(
            user=cls.user,
            chromosomeID=cls.chromosome,
            gene_name="S",
            gene_start=21563,
            gene_end=25384,
        )
        cls.filter = core.models.Filter.objects.create(filter="PASS")
        cls.effect = core.models.Effect.objects.create(effect="missense_variant")
        cls.variant = core.models.Variant.objects.create(
            chromosomeID_id=cls.chromosome,
            filterID_id=cls.filter,
            ref="A",
            pos="23063",
            alt="T",
        )
        cls.variant_in_sample = core.models.VariantInSample.objects.create(
            sampleID_id=cls.sample,
            variantID_id=cls.variant,
            bioinformatics_analysis_date="2026-06-23",
            dp="120",
            ref_dp="20",
            alt_dp="100",
            af=0.83,
        )
        cls.variant_annotation = core.models.VariantAnnotation.objects.create(
            geneID_id=cls.gene,
            effectID_id=cls.effect,
            variantID_id=cls.variant,
            hgvs_c="c.23063A>T",
            hgvs_p="p.N501Y",
            hgvs_p_1_letter="N501Y",
        )

    def test_reference_object_queries_cover_present_and_missing_values(self):
        self.assertEqual(
            list(core.utils.variants.get_all_chromosome_objs()),
            [self.chromosome],
        )
        self.assertEqual(
            list(core.utils.variants.get_all_organism_objs()),
            [self.annotation],
        )
        self.assertEqual(core.utils.variants.get_default_chromosome(), self.chromosome)
        self.assertEqual(
            core.utils.variants.get_gene_obj_from_gene_name("s"),
            self.gene,
        )
        self.assertIsNone(core.utils.variants.get_gene_obj_from_gene_name("missing"))
        self.assertEqual(
            core.utils.variants.get_if_organism_exists("NC_045512"),
            self.annotation,
        )
        self.assertIsNone(core.utils.variants.get_if_organism_exists("missing"))
        self.assertEqual(
            core.utils.variants.get_if_chromosomes_exists("NC_045512.2"),
            self.chromosome,
        )
        self.assertIsNone(core.utils.variants.get_if_chromosomes_exists("missing"))

    def test_gene_domain_and_variant_sample_lists_are_generated(self):
        self.assertEqual(
            core.utils.variants.get_gene_list(self.chromosome),
            ["S"],
        )
        self.assertEqual(
            core.utils.variants.get_domains_and_coordenates(self.chromosome),
            [{"name": "S", "coord": "21563-25384"}],
        )
        self.assertEqual(
            core.utils.variants.get_domains_list("NC_045512.2"),
            [{"name": "S", "coord": "21563-25384"}],
        )
        self.assertEqual(
            core.utils.variants.get_sample_in_variant_list(self.chromosome),
            [self.sample.sample_unique_id],
        )

    def test_variant_sample_vectors_include_frequency_effect_and_position(self):
        self.assertEqual(
            core.utils.variants.get_alelle_frequency_per_sample(
                self.sample.sequencing_sample_id,
                self.chromosome.chromosome,
            ),
            ["0.83"],
        )
        self.assertEqual(
            core.utils.variants.create_effect_list(
                self.sample.sequencing_sample_id,
                self.chromosome.chromosome,
            ),
            ["p.N501Y"],
        )
        self.assertEqual(
            core.utils.variants.get_position_per_sample(
                self.sample.sequencing_sample_id,
                self.chromosome.chromosome,
            ),
            ["23063"],
        )
        self.assertIsNone(
            core.utils.variants.get_alelle_frequency_per_sample(
                self.sample.sequencing_sample_id,
                "missing",
            )
        )
        self.assertEqual(
            core.utils.variants.create_effect_list(
                "missing",
                self.chromosome.chromosome,
            ),
            [],
        )

    def test_variant_table_data_handles_found_and_missing_samples(self):
        result = core.utils.variants.get_variant_data_from_sample(self.sample.pk)

        self.assertEqual(
            result["heading"],
            core.config.HEADING_FOR_VARIANT_TABLE_DISPLAY,
        )
        self.assertEqual(len(result["variant_data"]), 1)
        self.assertEqual(
            core.utils.variants.get_variant_data_from_sample(999999),
            {},
        )

    def test_empty_reference_queries_return_none_or_empty_lists(self):
        core.models.VariantAnnotation.objects.all().delete()
        core.models.VariantInSample.objects.all().delete()
        core.models.Gene.objects.all().delete()
        core.models.OrganismAnnotation.objects.all().delete()
        core.models.Chromosome.objects.all().delete()

        self.assertIsNone(core.utils.variants.get_all_chromosome_objs())
        self.assertIsNone(core.utils.variants.get_all_organism_objs())
        self.assertIsNone(core.utils.variants.get_default_chromosome())
        self.assertEqual(core.utils.variants.get_gene_list(self.chromosome), [])
        self.assertEqual(
            core.utils.variants.get_domains_and_coordenates(self.chromosome),
            [],
        )


class SampleGraphicsBranchTests(SimpleTestCase):
    @patch(
        "core.utils.samples_graphics.core.utils.plotly_graphics.bar_graphic",
        return_value="<div>ccaa</div>",
    )
    @patch(
        "core.utils.samples_graphics.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value={"x": ["Madrid"], "y": [3]},
    )
    def test_received_per_ccaa_uses_cached_data(self, _cached, graphic):
        result = core.utils.samples_graphics.received_per_ccaa()

        self.assertEqual(result, "<div>ccaa</div>")
        graphic.assert_called_once()

    @patch(
        "core.utils.samples_graphics.dashboard.utils.generic_process_data.pre_proc_samples_received_per_lab",
        return_value={"ERROR": "iSkyLIMS unavailable"},
    )
    @patch(
        "core.utils.samples_graphics.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value=None,
    )
    def test_received_per_lab_propagates_preprocessing_error(
        self,
        _cached,
        _preprocess,
    ):
        self.assertEqual(
            core.utils.samples_graphics.received_per_lab(),
            {"ERROR": "iSkyLIMS unavailable"},
        )

    @patch(
        "core.utils.samples_graphics.core.utils.plotly_graphics.line_graphic",
        return_value="<div>timeline</div>",
    )
    @patch(
        "core.utils.samples_graphics.core.utils.samples.get_all_recieved_samples_with_dates",
        return_value=[
            {datetime(2026, 1, 1).date(): 1},
            {datetime(2026, 1, 2).date(): 3},
        ],
    )
    def test_received_samples_graph_builds_accumulated_timeline(
        self,
        _received,
        line_graphic,
    ):
        result = core.utils.samples_graphics.received_samples_graph()

        self.assertEqual(result, "<div>timeline</div>")
        args = line_graphic.call_args.args
        self.assertEqual(args[1], [1, 3])
        self.assertEqual(args[2]["xaxis"]["type"], "date")


class AdditionalSchemaBranchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="schema-branch-owner")
        cls.schema = core.models.Schema.objects.create_new_schema(
            {
                "file_name": "schemas/branch.json",
                "user_name": cls.user,
                "schema_name": "BRANCH",
                "schema_version": "1.0",
                "schema_default": True,
                "schema_app_name": "core",
            }
        )
        cls.sample_class = core.models.Classification.objects.create(
            classification_name="Sample",
        )
        cls.sample_property = core.models.SchemaProperties.objects.create(
            schemaID=cls.schema,
            classificationID=cls.sample_class,
            property="sample_field",
            examples="example",
            ontology="TEST:1",
            type="string",
            description="Sample field",
            label="Sample Field",
            required=True,
            options=False,
            fill_mode="sample",
        )
        cls.batch_property = core.models.SchemaProperties.objects.create(
            schemaID=cls.schema,
            classificationID=cls.sample_class,
            property="batch_field",
            examples="example",
            ontology="TEST:2",
            type="string",
            description="Batch field",
            label="Batch Field",
            required=False,
            options=False,
            fill_mode="batch",
        )

    def test_metadata_visualization_fetch_groups_sample_and_batch_fields(self):
        self.assertIsNone(core.utils.schema.fetch_info_meta_visualization(self.schema))
        core.models.MetadataVisualization.objects.create_metadata_visualization(
            {
                "schema_id": self.schema,
                "property_name": "sample_field",
                "label_name": "Sample Field",
                "order": 2,
                "in_use": True,
                "fill_mode": "sample",
            }
        )
        core.models.MetadataVisualization.objects.create_metadata_visualization(
            {
                "schema_id": self.schema,
                "property_name": "batch_field",
                "label_name": "Batch Field",
                "order": 1,
                "in_use": True,
                "fill_mode": "batch",
            }
        )

        result = core.utils.schema.fetch_info_meta_visualization(self.schema)

        self.assertEqual(result["sample"], [["Sample Field", "2"]])
        self.assertEqual(result["batch"], [["Batch Field", "1"]])

    @patch(
        "core.utils.schema.get_fields_if_template",
        return_value=["Batch Field"],
    )
    def test_fields_from_schema_marks_template_selection_and_order(self, _template):
        result = core.utils.schema.get_fields_from_schema(self.schema)
        rows = {row[0]: row for row in result["fields"]}

        self.assertEqual(result["schema_id"], str(self.schema.pk))
        self.assertEqual(rows["batch_field"][2:4], [0, "true"])
        self.assertEqual(rows["sample_field"][3], "false")

    def test_schema_lookup_helpers_cover_found_and_missing_records(self):
        self.assertEqual(
            core.utils.schema.get_latest_schema("branch", "core"),
            self.schema,
        )
        self.assertIn(
            "ERROR",
            core.utils.schema.get_latest_schema("missing", "core"),
        )
        self.assertEqual(
            core.utils.schema.get_schema_obj_from_id(self.schema.pk),
            self.schema,
        )
        self.assertIsNone(core.utils.schema.get_schema_obj_from_id(999999))
        self.assertEqual(core.utils.schema.get_default_schema(), self.schema)
        self.assertEqual(len(core.utils.schema.get_schemas_loaded("core")), 1)
        self.assertEqual(core.utils.schema.get_schemas_loaded("missing"), [])

    def test_schema_display_and_property_helpers_return_structured_data(self):
        displayed = core.utils.schema.get_schema_display_data(self.schema.pk)
        properties = core.utils.schema.get_schema_properties(self.schema)

        self.assertEqual(
            displayed["heading"],
            core.config.HEADING_SCHEMA_DISPLAY,
        )
        self.assertEqual(len(displayed["s_data"]), 2)
        self.assertEqual(
            properties["sample_field"],
            {"classification": "Sample", "ontology": "TEST:1"},
        )
        self.assertEqual(
            core.utils.schema.get_schema_display_data(999999),
            {"ERROR": core.config.ERROR_SCHEMA_ID_NOT_DEFINED},
        )

    def test_delete_metadata_visualization_covers_empty_and_populated_states(self):
        self.assertIsNone(core.utils.schema.del_metadata_visualization())
        core.models.MetadataVisualization.objects.create_metadata_visualization(
            {
                "schema_id": self.schema,
                "property_name": "sample_field",
                "label_name": "Sample Field",
                "order": 1,
                "in_use": True,
                "fill_mode": "sample",
            }
        )

        self.assertIsNone(core.utils.schema.del_metadata_visualization())
        self.assertFalse(core.models.MetadataVisualization.objects.exists())

    def test_remove_existing_default_schema_only_changes_matching_schema(self):
        core.utils.schema.remove_existing_default_schema("BRANCH", "core")
        self.schema.refresh_from_db()
        self.assertFalse(self.schema.schema_default)

        core.utils.schema.remove_existing_default_schema("missing", "core")
        self.schema.refresh_from_db()
        self.assertFalse(self.schema.schema_default)

    @patch(
        "core.utils.schema.load_schema",
        return_value={"ERROR": "Invalid JSON"},
    )
    def test_process_schema_propagates_load_error(self, _load):
        self.assertEqual(
            core.utils.schema.process_schema_file(
                MagicMock(),
                "off",
                self.user,
                "core",
            ),
            {"ERROR": "Invalid JSON"},
        )

    @patch(
        "core.utils.schema.load_schema",
        return_value={
            "file_name": "schemas/invalid.json",
            "full_schema": {"type": "object"},
        },
    )
    def test_process_schema_rejects_missing_required_headings(self, _load):
        self.assertEqual(
            core.utils.schema.process_schema_file(
                MagicMock(),
                "off",
                self.user,
                "core",
            ),
            {"ERROR": core.config.ERROR_INVALID_SCHEMA},
        )

    @patch(
        "core.utils.schema.load_schema",
        return_value={
            "file_name": "schemas/duplicate.json",
            "full_schema": {
                "$schema": "test",
                "required": [],
                "type": "object",
                "properties": {},
                "title": "BRANCH",
                "version": "1.0",
            },
        },
    )
    def test_process_schema_rejects_duplicate_name_and_version(self, _load):
        self.assertEqual(
            core.utils.schema.process_schema_file(
                MagicMock(),
                "off",
                self.user,
                "core",
            ),
            {"ERROR": core.config.ERROR_SCHEMA_ALREADY_LOADED},
        )


class GenericAndLaboratoryBranchTests(TestCase):
    def test_configuration_and_defined_user_helpers_cover_empty_and_present_values(self):
        self.assertEqual(
            core.utils.generic_functions.get_configuration_value("MISSING"),
            "False",
        )
        setting = core.models.ConfigSetting.objects.create(
            configuration_name="SETTING",
            configuration_value="value",
        )
        admin = User.objects.create_user(username="admin")
        alice = User.objects.create_user(username="alice")

        self.assertEqual(
            core.utils.generic_functions.get_configuration_value("SETTING"),
            "value",
        )
        self.assertEqual(
            core.utils.generic_functions.get_defined_users(),
            [[alice.pk, "alice"]],
        )
        setting.set_configuration_value("updated")
        self.assertEqual(setting.get_configuration_value(), "updated")
        self.assertNotIn(admin.pk, [item[0] for item in core.utils.generic_functions.get_defined_users()])

    def test_user_lab_field_and_group_filter_cover_role_and_missing_group(self):
        user = User.objects.create_user(username="collector-filter")
        collector = Group.objects.create(name="Collector")
        user.groups.add(collector)

        self.assertEqual(
            core.utils.generic_functions.get_user_lab_field(user),
            "lab_code_1",
        )
        self.assertTrue(has_group(user, "Collector"))
        self.assertFalse(has_group(user, "Missing"))

    @patch(
        "core.utils.labs.core.utils.rest_api.get_laboratory_data",
        return_value={"ERROR": "Unavailable"},
    )
    def test_lab_contact_returns_empty_without_lab_and_propagates_api_error(
        self,
        _laboratory_data,
    ):
        no_lab = User.objects.create_user(username="no-lab")
        with_lab = User.objects.create_user(username="with-lab")
        core.models.Profile.objects.filter(user=with_lab).update(
            laboratory="Hospital A"
        )

        self.assertEqual(core.utils.labs.get_lab_contact_details(no_lab), "")
        self.assertEqual(
            core.utils.labs.get_lab_contact_details(with_lab),
            "Unavailable",
        )

    @patch(
        "core.utils.labs.core.utils.rest_api.get_summarize_data",
        side_effect=[
            {"ERROR": "Unavailable"},
            {"laboratory": {"Lab A": {}, "Lab B": {}}},
        ],
    )
    def test_defined_labs_propagate_error_or_return_names(self, _summary):
        self.assertEqual(
            core.utils.labs.get_all_defined_labs(),
            {"ERROR": "Unavailable"},
        )
        self.assertEqual(
            core.utils.labs.get_all_defined_labs(),
            ["Lab A", "Lab B"],
        )

    @patch(
        "core.utils.labs.core.utils.rest_api.set_laboratory_data",
        return_value={"ERROR": "Update failed"},
    )
    def test_contact_update_propagates_external_error(self, _update):
        self.assertEqual(
            core.utils.labs.update_contact_lab({"lab_name": "Hospital A"}),
            {"ERROR": "Update failed"},
        )


class RestApiAdapterTests(SimpleTestCase):
    def setUp(self):
        self.api = MagicMock()
        self.api_class = patch(
            "core.utils.rest_api.relecov_tools.rest_api.RestApi",
            return_value=self.api,
        )
        self.api_class.start()
        self.addCleanup(self.api_class.stop)
        self.configuration = patch(
            "core.utils.rest_api.core.utils.generic_functions.get_configuration_value",
            side_effect=lambda name: {
                "ISKYLIMS_SERVER": "https://iskylims.example",
                "ISKYLIMS_USER": "api-user",
                "ISKYLIMS_PASSWORD": "api-password",
            }.get(name, "False"),
        )
        self.configuration.start()
        self.addCleanup(self.configuration.stop)

    def test_create_get_api_instance_supports_scalar_and_dictionary_requests(self):
        self.api.get_request.side_effect = [
            {"data": "scalar"},
            {"data": "dictionary"},
        ]

        scalar = core.utils.rest_api.create_get_api_instance(
            ("sample-info", "sample"),
            "SAMPLE-1",
        )
        dictionary = core.utils.rest_api.create_get_api_instance(
            ("project-fields",),
            {"project": "RELECOV"},
        )

        self.assertEqual(scalar, {"data": "scalar"})
        self.assertEqual(dictionary, {"data": "dictionary"})
        self.api.get_request.assert_any_call("sample-info", "sample", "SAMPLE-1")
        self.api.get_request.assert_any_call(
            "project-fields",
            {"project": "RELECOV"},
            {"project": "RELECOV"},
        )

    def test_fetch_and_laboratory_requests_wrap_external_errors(self):
        self.api.get_request.side_effect = [
            {"ERROR": "fetch failed"},
            {"ERROR": "lab failed"},
        ]

        fetched = core.utils.rest_api.fetch_samples_on_condition("collection_date")
        laboratory = core.utils.rest_api.get_laboratory_data("Hospital A")

        self.assertEqual(fetched, {"ERROR": {"ERROR": "fetch failed"}})
        self.assertEqual(laboratory, {"ERROR": {"ERROR": "lab failed"}})

    def test_credentials_and_laboratory_update_cover_success_and_error(self):
        self.assertEqual(
            core.utils.rest_api.get_user_credentials(),
            {"user": "api-user", "pass": "api-password"},
        )
        self.api.put_request.side_effect = [
            {"updated": True},
            {"ERROR": "update failed"},
        ]

        success = core.utils.rest_api.set_laboratory_data({"lab_name": "Hospital A"})
        error = core.utils.rest_api.set_laboratory_data({"lab_name": "Hospital B"})

        self.assertEqual(success, {"updated": True})
        self.assertEqual(error, {"ERROR": {"ERROR": "update failed"}})

    def test_sample_fields_information_and_parameters_unwrap_success_payloads(self):
        self.api.get_request.return_value = {"data": [{"field": "sample_id"}]}
        fields = core.utils.rest_api.get_sample_fields_data()
        self.assertEqual(fields, [{"field": "sample_id"}])

        with patch(
            "core.utils.rest_api.create_get_api_instance",
            side_effect=[
                {"data": {"sample": "S1"}},
                {"data": [1, 2]},
                {"data": [3, 4]},
            ],
        ):
            sample = core.utils.rest_api.get_sample_information("S1")
            scalar = core.utils.rest_api.get_sample_parameter_data("field")
            dictionary = core.utils.rest_api.get_sample_parameter_data(
                {"project": "RELECOV"}
            )

        self.assertEqual(sample, {"sample": "S1"})
        self.assertEqual(scalar, [1, 2])
        self.assertEqual(dictionary, [3, 4])

    def test_project_field_display_map_handles_labels_fallbacks_and_empty_inputs(self):
        self.assertEqual(
            core.utils.rest_api.get_sample_project_field_display_map(None),
            {},
        )
        with patch(
            "core.utils.rest_api.get_sample_project_fields_data",
            return_value=[
                {
                    "sample_project_field_name": "field_a",
                    "sample_project_field_description": "Field A",
                },
                {
                    "sample_project_field_name": "field_b",
                    "sample_project_field_description": "",
                },
                {"sample_project_field_description": "Missing key"},
            ],
        ):
            result = core.utils.rest_api.get_sample_project_field_display_map(
                {"value": "RELECOV"}
            )

        self.assertEqual(
            result,
            {"field_a": "Field A", "field_b": "field_b"},
        )

    def test_summary_stats_and_post_requests_cover_success_and_error(self):
        self.api.get_request.side_effect = [
            {"data": {"laboratory": {"A": 1}}},
            {"ERROR": "stats failed"},
        ]
        self.api.post_request.side_effect = [
            {"data": {"saved": True}},
            {"ERROR": "save failed"},
        ]

        summary = core.utils.rest_api.get_summarize_data(None)
        stats = core.utils.rest_api.get_stats_data({"field": "value"})
        saved = core.utils.rest_api.save_sample_form_data(
            {"sample": "S1"},
            {"user": "u", "pass": "p"},
        )
        failed = core.utils.rest_api.save_sample_form_data(
            {"sample": "S2"},
            {"user": "u", "pass": "p"},
        )

        self.assertEqual(summary, {"laboratory": {"A": 1}})
        self.assertEqual(stats, {"ERROR": "stats failed"})
        self.assertEqual(saved, {"saved": True})
        self.assertEqual(failed, {"ERROR": "save failed"})


class CoreViewBranchTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = SimpleNamespace(username="admin", is_authenticated=True)
        self.user = SimpleNamespace(username="user", is_authenticated=True)

    @patch("core.views.core.utils.labs.get_lab_name_from_user")
    @patch("core.views.core.utils.samples.get_search_table_for_user")
    @patch("core.views.core.models.Sample.objects.count")
    def test_search_rows_report_empty_database_and_user_lab_filters(
        self, sample_count, get_table, get_lab
    ):
        sample_count.return_value = 0
        self.assertEqual(
            _get_search_sample_rows_for_user(self.user),
            {"ERROR": core.config.ERROR_NOT_SAMPLES_HAVE_BEEN_DEFINED},
        )

        sample_count.return_value = 1
        get_table.return_value = {"ERROR": "cache unavailable"}
        self.assertEqual(
            _get_search_sample_rows_for_user(self.user),
            {"ERROR": "cache unavailable"},
        )

        get_table.return_value = []
        get_lab.return_value = ""
        self.assertEqual(
            _get_search_sample_rows_for_user(self.user),
            {"ERROR": "You don't have a laboratory assigned to you yet"},
        )

        get_lab.return_value = "Hospital A"
        self.assertEqual(
            _get_search_sample_rows_for_user(self.user),
            {
                "ERROR": (
                    "No samples found for your designated laboratory: Hospital A"
                )
            },
        )

    @patch("core.views.core.utils.samples.get_search_table_for_user")
    @patch("core.views.core.models.Sample.objects.count", return_value=2)
    def test_search_rows_convert_tuple_summary_to_datatable_rows(
        self, _sample_count, get_table
    ):
        get_table.return_value = [
            (1, "SEQ-1", "2024-01-01", "XFG.3", "Hospital A")
        ]

        self.assertEqual(
            _get_search_sample_rows_for_user(self.user),
            [
                {
                    "id": 1,
                    "sequencing_id": "SEQ-1",
                    "collection_date": "2024-01-01",
                    "lineage": "XFG.3",
                    "collecting_institution": "Hospital A",
                }
            ],
        )

    def test_datatable_matching_and_sort_helpers_cover_negative_branches(self):
        row = {
            "sequencing_id": "SEQ-1",
            "collection_date": "2024-01-01",
            "lineage": "XFG.3",
            "collecting_institution": None,
        }

        self.assertFalse(_row_matches_search(row, "missing", []))
        self.assertFalse(
            _row_matches_search(
                row,
                "",
                [("lineage", "JN.1", True)],
            )
        )
        self.assertFalse(
            _row_matches_search(
                row,
                "",
                [("sequencing_id", "SEQ-2", False)],
            )
        )
        self.assertEqual(_get_sort_value({"field": None}, "field"), "")
        self.assertEqual(_get_sort_value({"field": "ABC"}, "field"), "abc")
        self.assertEqual(_get_sort_value({"field": 5}, "field"), 5)

    @patch("core.views.render")
    @patch("core.views.core.utils.generic_functions.get_configuration_value")
    @patch("core.views.core.utils.samples.count_handled_samples")
    def test_index_renders_sample_count_and_nextstrain_url(
        self, count_samples, get_config, render
    ):
        request = self.factory.get("/")
        count_samples.return_value = {"Defined": 10}
        get_config.return_value = "https://nextstrain.example"

        core.views.index(request)

        render.assert_called_once_with(
            request,
            "core/index.html",
            {
                "number_of_samples": {"Defined": 10},
                "nextstrain_url": "https://nextstrain.example",
            },
        )

    @patch("core.views.redirect")
    def test_assign_samples_redirects_non_admin(self, redirect):
        request = self.factory.get("/assignSamples")
        request.user = self.user

        core.views.assign_samples_to_user(request)

        redirect.assert_called_once_with("/")

    @patch("core.views.render")
    @patch("core.views.core.utils.samples.assign_samples_to_new_user")
    def test_assign_samples_posts_assignment_for_admin(self, assign_samples, render):
        request = self.factory.post(
            "/assignSamples",
            {"action": "assignSamples", "sample": "S1"},
        )
        request.user = self.admin
        assign_samples.return_value = {"SUCCESS": "assigned"}

        core.views.assign_samples_to_user(request)

        render.assert_called_once_with(
            request,
            "core/assignSamplesToUser.html",
            {"SUCCESS": "assigned"},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.generic_functions.get_defined_users")
    @patch("core.views.core.utils.labs.get_all_defined_labs")
    def test_assign_samples_get_renders_labs_and_users(
        self, get_labs, get_users, render
    ):
        request = self.factory.get("/assignSamples")
        request.user = self.admin
        get_labs.return_value = ["Lab A"]
        get_users.return_value = ["alice"]

        core.views.assign_samples_to_user(request)

        render.assert_called_once_with(
            request,
            "core/assignSamplesToUser.html",
            {"lab_data": {"labs": ["Lab A"], "users": ["alice"]}},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.samples.get_sample_display_data",
        return_value={"ERROR": "Not found"},
    )
    def test_sample_display_renders_error(self, _sample_data, render):
        request = self.factory.get("/sampleDisplay=1")
        request.user = self.user

        core.views.sample_display(request, 1)

        render.assert_called_once_with(
            request,
            "core/sampleDisplay.html",
            {"ERROR": "Not found"},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.variants.get_variant_graphic_from_sample",
        return_value="variant graphic",
    )
    @patch(
        "core.views.core.utils.variants.get_variant_data_from_sample",
        return_value={"heading": "Variants"},
    )
    @patch(
        "core.views.core.utils.lineage.get_lineage_data_from_sample",
        return_value={"lineage": "XFG.3"},
    )
    @patch(
        "core.views.core.utils.bioinfo_analysis.get_bioinfo_analysis_data_from_sample",
        return_value={"depth": 100},
    )
    @patch(
        "core.views.core.utils.public_db.get_public_information_from_sample",
        side_effect=[{"gisaid": "EPI"}, {"ena": "ERS"}],
    )
    @patch(
        "core.views.core.utils.samples.get_sample_display_data",
        return_value={"sample": "S1"},
    )
    def test_sample_display_enriches_successful_sample_context(
        self,
        _sample_data,
        _public_data,
        _bioinfo,
        _lineage,
        _variant,
        _graphic,
        render,
    ):
        request = self.factory.get("/sampleDisplay=1")
        request.user = self.user

        core.views.sample_display(request, 1)

        context = render.call_args.args[2]["sample_data"]
        self.assertEqual(context["gisaid"], {"gisaid": "EPI"})
        self.assertEqual(context["ena"], {"ena": "ERS"})
        self.assertEqual(context["lineage"], {"lineage": "XFG.3"})
        self.assertEqual(context["graphic"], "variant graphic")

    @patch("core.views.redirect")
    def test_schema_views_redirect_non_admin_users(self, redirect):
        request = self.factory.get("/schemaHandling")
        request.user = self.user

        core.views.schema_handling(request)
        core.views.schema_display(request, 1)

        self.assertEqual(redirect.call_count, 2)
        redirect.assert_called_with("/")

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.schema.get_schemas_loaded",
        return_value=["schema-v1"],
    )
    def test_schema_handling_get_renders_loaded_schemas(self, _schemas, render):
        request = self.factory.get("/schemaHandling")
        request.user = self.admin

        core.views.schema_handling(request)

        render.assert_called_once_with(
            request,
            "core/schemaHandling.html",
            {"schemas": ["schema-v1"]},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.schema.process_schema_file",
        return_value={"ERROR": "Invalid schema"},
    )
    def test_schema_handling_upload_error(self, _process_schema, render):
        request = self.factory.post(
            "/schemaHandling",
            {"action": "uploadSchema"},
        )
        request.user = self.admin
        request.FILES["schemaFile"] = MagicMock()

        core.views.schema_handling(request)

        render.assert_called_once_with(
            request,
            "core/schemaHandling.html",
            {"ERROR": "Invalid schema"},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.schema.get_schemas_loaded",
        return_value=["schema-v1"],
    )
    @patch(
        "core.views.core.utils.schema.process_schema_file",
        return_value={"SUCCESS": "Schema loaded"},
    )
    def test_schema_handling_upload_success(self, _process_schema, _schemas, render):
        request = self.factory.post(
            "/schemaHandling",
            {"action": "uploadSchema", "schemaDefault": "on"},
        )
        request.user = self.admin
        request.FILES["schemaFile"] = MagicMock()

        core.views.schema_handling(request)

        render.assert_called_once_with(
            request,
            "core/schemaHandling.html",
            {"SUCCESS": "Schema loaded", "schemas": ["schema-v1"]},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.schema.get_schema_display_data",
        return_value={"schema": "v1"},
    )
    def test_schema_display_renders_schema_data(self, _schema_data, render):
        request = self.factory.get("/schemaDisplay=1")
        request.user = self.admin

        core.views.schema_display(request, 1)

        render.assert_called_once_with(
            request,
            "core/schemaDisplay.html",
            {"schema_data": {"schema": "v1"}},
        )

    @patch("core.views.render")
    @patch(
        "core.views._get_search_sample_rows_for_user",
        return_value={"ERROR": "No samples"},
    )
    def test_search_sample_renders_error_and_empty_filter_options(
        self, _rows, render
    ):
        request = self.factory.get("/searchSample")
        request.user = self.user

        core.views.search_sample(request)

        render.assert_called_once_with(
            request,
            "core/searchSample.html",
            {
                "ERROR": "No samples",
                "lineage_options": [],
                "collecting_institution_options": [],
            },
        )

    @patch("core.views.render")
    @patch("core.views._get_search_sample_rows_for_user")
    def test_search_sample_renders_sorted_filter_options(self, get_rows, render):
        request = self.factory.get("/searchSample")
        request.user = self.user
        get_rows.return_value = [
            {
                "lineage": "XFG.3",
                "collecting_institution": "Hospital B",
            },
            {
                "lineage": "JN.1",
                "collecting_institution": "Hospital A",
            },
            {"lineage": "", "collecting_institution": ""},
        ]

        core.views.search_sample(request)

        render.assert_called_once_with(
            request,
            "core/searchSample.html",
            {
                "lineage_options": ["JN.1", "XFG.3"],
                "collecting_institution_options": ["Hospital A", "Hospital B"],
            },
        )

    @patch("core.views._get_search_sample_rows_for_user")
    def test_search_sample_data_handles_invalid_pagination_and_all_rows(
        self, get_rows
    ):
        get_rows.return_value = [
            {
                "id": 1,
                "sequencing_id": "SEQ-1",
                "collection_date": "2024-01-01",
                "lineage": "XFG.3",
                "collecting_institution": "Hospital A",
            }
        ]
        request = self.factory.get(
            "/searchSample/data",
            {
                "draw": "bad",
                "start": "bad",
                "length": "-1",
                "order[0][column]": "bad",
            },
        )
        request.user = self.user

        response = core.views.search_sample_data(request)
        payload = json.loads(response.content)

        self.assertEqual(payload["draw"], 0)
        self.assertEqual(payload["recordsFiltered"], 1)
        self.assertEqual(payload["data"][0]["sequencing_id"], "SEQ-1")

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.schema.store_fields_metadata_visualization",
        return_value={"ERROR": "Select at least one field"},
    )
    @patch(
        "core.views.core.utils.schema.get_fields_from_schema",
        return_value=["field-a"],
    )
    @patch("core.views.core.utils.schema.get_schema_obj_from_id")
    def test_metadata_visualization_select_fields_error(
        self, _schema_obj, _fields, _store, render
    ):
        request = self.factory.post(
            "/metadataVisualization",
            {"action": "selectFields", "schemaID": "1"},
        )
        request.user = self.admin

        core.views.metadata_visualization(request)

        render.assert_called_once_with(
            request,
            "core/metadataVisualization.html",
            {
                "ERROR": {"ERROR": "Select at least one field"},
                "m_visualization": ["field-a"],
            },
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.schema.store_fields_metadata_visualization",
        return_value={"SUCCESS": "stored"},
    )
    def test_metadata_visualization_select_fields_success(self, _store, render):
        request = self.factory.post(
            "/metadataVisualization",
            {"action": "selectFields", "schemaID": "1"},
        )
        request.user = self.admin

        core.views.metadata_visualization(request)

        render.assert_called_once_with(
            request,
            "core/metadataVisualization.html",
            {"SUCCESS": {"SUCCESS": "stored"}},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.schema.del_metadata_visualization")
    def test_metadata_visualization_delete_fields(self, delete_fields, render):
        request = self.factory.post(
            "/metadataVisualization",
            {"action": "deleteFields"},
        )
        request.user = self.admin

        core.views.metadata_visualization(request)

        delete_fields.assert_called_once_with()
        render.assert_called_once_with(
            request,
            "core/metadataVisualization.html",
            {"DELETE": "DELETE"},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.schema.get_latest_schema",
        return_value={"ERROR": "No schema"},
    )
    def test_metadata_visualization_get_reports_missing_schema(
        self, _schema, render
    ):
        request = self.factory.get("/metadataVisualization")
        request.user = self.admin

        core.views.metadata_visualization(request)

        render.assert_called_once_with(
            request,
            "core/metadataVisualization.html",
            {"ERROR": "No schema"},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.schema.fetch_info_meta_visualization",
        return_value={"selected": ["field-a"]},
    )
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_visualization_get_existing_selection(
        self, _schema, _visualization, render
    ):
        request = self.factory.get("/metadataVisualization")
        request.user = self.admin

        core.views.metadata_visualization(request)

        render.assert_called_once_with(
            request,
            "core/metadataVisualization.html",
            {"data_visualization": {"selected": ["field-a"]}},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.schema.get_fields_from_schema",
        return_value=["field-a"],
    )
    @patch(
        "core.views.core.utils.schema.fetch_info_meta_visualization",
        return_value=[],
    )
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_visualization_get_available_schema_fields(
        self, _schema, _visualization, _fields, render
    ):
        request = self.factory.get("/metadataVisualization")
        request.user = self.admin

        core.views.metadata_visualization(request)

        render.assert_called_once_with(
            request,
            "core/metadataVisualization.html",
            {"m_visualization": ["field-a"]},
        )

    @patch("core.views.render")
    def test_variants_renders_static_template(self, render):
        request = self.factory.get("/variants")

        core.views.variants(request)

        render.assert_called_once_with(request, "core/variants.html", {})

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.samples.get_sample_per_date_per_all_lab",
        return_value={"ERROR": "No preprocessed data"},
    )
    @patch("core.views.Group.objects.filter")
    def test_intranet_renders_preprocessing_error(self, group_filter, _samples, render):
        group_filter.return_value.last.return_value = object()
        request = self.factory.get("/intranet")
        request.user = SimpleNamespace(
            username="collector",
            is_authenticated=True,
            groups=SimpleNamespace(all=lambda: []),
        )

        core.views.intranet(request)

        render.assert_called_once_with(
            request,
            "core/intranet.html",
            {"ERROR": "No preprocessed data"},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.generic_functions.get_user_lab_field")
    @patch("core.views.core.utils.labs.get_lab_codes_from_user", return_value=[])
    @patch("core.views.core.utils.labs.get_lab_name_from_user", return_value="Lab A")
    @patch("core.views.core.utils.generic_functions.get_user_role", return_value="Collector")
    @patch("core.views.core.utils.samples.get_sample_per_date_per_all_lab")
    @patch("core.views.Group.objects.filter")
    def test_intranet_non_manager_without_lab_field_returns_empty_context(
        self,
        group_filter,
        get_samples,
        _role,
        _lab_name,
        _lab_codes,
        get_lab_field,
        render,
    ):
        group_filter.return_value.last.return_value = object()
        get_samples.return_value = [
            {"iso_yearweek": "2024-W01", "num_samples": 2, "lab_code_1": "LAB-01"}
        ]
        get_lab_field.return_value = ""
        request = self.factory.get("/intranet")
        request.user = SimpleNamespace(
            username="collector",
            is_authenticated=True,
            groups=SimpleNamespace(all=lambda: []),
        )

        core.views.intranet(request)

        render.assert_called_once_with(
            request,
            "core/intranet.html",
            {"intra_data": {}},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.public_db.percentage_graphic", return_value="percentage")
    @patch("core.views.core.utils.public_db.get_preprocessed_ena_data")
    @patch("core.views.core.utils.public_db.get_preprocessed_gisaid_data")
    @patch("core.views.core.utils.samples.get_lab_last_actions", return_value=["action"])
    @patch("core.views.core.utils.samples.create_dash_bar_for_each_lab", return_value="per-lab")
    @patch("core.views.core.utils.samples.fancy_gauge_graphic", return_value="gauge")
    @patch("core.views.core.utils.samples.create_date_sample_bar", return_value="bar")
    @patch("core.views.core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab")
    @patch("core.views.core.utils.samples.get_sample_objs_per_lab", return_value=[object(), object()])
    @patch("core.views.core.utils.labs.get_display_name_from_code", return_value="Hospital A")
    @patch("core.views.core.utils.generic_functions.get_user_lab_field", return_value="lab_code_1")
    @patch("core.views.core.utils.labs.get_lab_codes_from_user", return_value=["LAB-01"])
    @patch("core.views.core.utils.labs.get_lab_name_from_user", return_value="Hospital A")
    @patch("core.views.core.utils.generic_functions.get_user_role", return_value="Collector")
    @patch("core.views.core.utils.samples.get_sample_per_date_per_all_lab")
    @patch("core.views.Group.objects.filter")
    def test_intranet_non_manager_builds_lab_context(
        self,
        group_filter,
        get_samples,
        _role,
        _lab_name,
        _lab_codes,
        _lab_field,
        _display_name,
        _sample_objs,
        analysis_stats,
        _bar,
        _gauge,
        _per_lab,
        _actions,
        gisaid,
        ena,
        _percentage,
        render,
    ):
        group_filter.return_value.last.return_value = object()
        get_samples.return_value = [
            {
                "iso_yearweek": "2024-W01",
                "num_samples": 2,
                "lab_code_1": "LAB-01",
                "collecting_institution": "Hospital A",
                "legacy_collecting_institution": "Old Hospital A",
                "submitting_institution": "Submitter",
            },
            {
                "iso_yearweek": "2024-W02",
                "num_samples": 3,
                "lab_code_1": "LAB-02",
                "collecting_institution": "Hospital B",
                "legacy_collecting_institution": "Old Hospital B",
                "submitting_institution": "Submitter",
            },
        ]
        analysis_stats.return_value = {"analized": 1, "received": 2}
        gisaid.return_value = {"Hospital A": [("G1",)]}
        ena.return_value = {"Hospital A": [("E1",)]}
        request = self.factory.get("/intranet")
        request.user = SimpleNamespace(
            username="collector",
            is_authenticated=True,
            groups=SimpleNamespace(all=lambda: []),
        )

        core.views.intranet(request)

        intra_data = render.call_args.args[2]["intra_data"]
        self.assertEqual(intra_data["lab"], "Hospital A")
        self.assertEqual(intra_data["sample_bar_graph"], "bar")
        self.assertEqual(intra_data["sample_gauge_graph"], "gauge")
        self.assertFalse(intra_data["show_per_lab_dash"])
        self.assertEqual(intra_data["gisaid_accession"], [("G1",)])
        self.assertEqual(intra_data["ena_accession"], [("E1",)])

    @patch("core.views.render")
    @patch("core.views.core.utils.public_db.percentage_graphic", return_value="percentage")
    @patch("core.views.core.utils.public_db.get_preprocessed_ena_data")
    @patch("core.views.core.utils.public_db.get_preprocessed_gisaid_data")
    @patch("core.views.core.utils.samples.get_lab_last_actions", return_value=["actions"])
    @patch("core.views.core.utils.samples.create_dash_bar_for_each_lab", return_value="per-lab")
    @patch("core.views.core.utils.samples.get_all_collecting_insts", return_value=[{"value": "LAB-01", "label": "Hospital A"}])
    @patch("core.views.core.utils.samples.fancy_gauge_graphic", return_value="gauge")
    @patch("core.views.core.utils.bioinfo_analysis.get_bio_analysis_stats_from_lab")
    @patch("core.views.core.utils.samples.create_date_sample_bar", return_value="bar")
    @patch("core.views.core.utils.samples.count_handled_samples", return_value={"Defined": 5})
    @patch("core.views.core.utils.samples.get_sample_per_date_per_all_lab")
    @patch("core.views.Group.objects.filter")
    def test_intranet_manager_builds_global_context(
        self,
        group_filter,
        get_samples,
        _count,
        _bar,
        analysis_stats,
        _gauge,
        _all_labs,
        _per_lab,
        _actions,
        gisaid,
        ena,
        _percentage,
        render,
    ):
        manager_group = object()
        group_filter.return_value.last.return_value = manager_group
        get_samples.return_value = [
            {
                "iso_yearweek": "2018-W01",
                "num_samples": 99,
                "submitting_institution": "Old",
            },
            {
                "iso_yearweek": "bad-week",
                "num_samples": 99,
                "submitting_institution": "Bad",
            },
            {
                "iso_yearweek": "2024-W01",
                "num_samples": 4,
                "submitting_institution": "Submitter",
                "collecting_institution": "Hospital A",
            },
        ]
        analysis_stats.return_value = {"analized": 3, "received": 4}
        gisaid.return_value = {"Lab A": [("G1",)]}
        ena.return_value = {"Lab A": [("E1",)]}
        request = self.factory.get("/intranet")
        request.user = SimpleNamespace(
            username="manager",
            is_authenticated=True,
            groups=SimpleNamespace(all=lambda: [manager_group]),
        )

        core.views.intranet(request)

        manager_data = render.call_args.args[2]["manager_intra_data"]
        self.assertEqual(manager_data["sample_bar_graph"], "bar")
        self.assertEqual(manager_data["sample_gauge_graph"], "gauge")
        self.assertEqual(manager_data["sample_per_lab_initial_arguments"], "per-lab")
        self.assertEqual(manager_data["gisaid_accession"], [("Lab A", "G1")])
        self.assertEqual(manager_data["ena_accession"], [("Lab A", "E1")])

    @patch("core.views.render")
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    @patch("core.views.core.utils.samples.save_excel_form_in_samba_folder")
    def test_metadata_form_upload_file_records_submission(
        self, save_file, _schema, render
    ):
        request = self.factory.post(
            "/metadataForm",
            {"action": "uploadMetadataFile"},
        )
        request.user = self.user
        request.FILES["metadataFile"] = MagicMock()

        core.views.metadata_form(request)

        save_file.assert_called_once()
        render.assert_called_once_with(
            request,
            "core/metadataForm.html",
            {"sample_recorded": {"ok": "OK"}},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.samples.create_metadata_form", return_value={"form": "metadata"})
    @patch("core.views.core.utils.samples.analyze_input_samples", return_value={})
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_form_define_samples_empty_analysis_returns_form(
        self, _schema, _analyze, _form, render
    ):
        request = self.factory.post("/metadataForm", {"action": "defineSamples"})
        request.user = self.user

        core.views.metadata_form(request)

        render.assert_called_once_with(
            request,
            "core/metadataForm.html",
            {"m_form": {"form": "metadata"}},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.samples.create_metadata_form", return_value={"form": "metadata"})
    @patch(
        "core.views.core.utils.samples.analyze_input_samples",
        return_value={"s_incomplete": ["S1"]},
    )
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_form_define_samples_renders_sample_issues(
        self, _schema, _analyze, _form, render
    ):
        request = self.factory.post("/metadataForm", {"action": "defineSamples"})
        request.user = self.user

        core.views.metadata_form(request)

        render.assert_called_once_with(
            request,
            "core/metadataForm.html",
            {
                "sample_issues": {"s_incomplete": ["S1"]},
                "m_form": {"form": "metadata"},
            },
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.samples.get_sample_pre_recorded", return_value=["S1"])
    @patch("core.views.core.utils.samples.create_form_for_batch", return_value={"batch": "form"})
    @patch("core.views.core.utils.samples.save_temp_sample_data", return_value={"saved": 1})
    @patch(
        "core.views.core.utils.samples.analyze_input_samples",
        return_value={"save_samples": ["S1"]},
    )
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_form_define_samples_success_builds_batch_form(
        self, _schema, _analyze, _save_temp, _batch_form, _pre_recorded, render
    ):
        request = self.factory.post("/metadataForm", {"action": "defineSamples"})
        request.user = self.user

        core.views.metadata_form(request)

        render.assert_called_once_with(
            request,
            "core/metadataForm.html",
            {"m_batch_form": {"batch": "form"}, "sample_saved": {"saved": 1}},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.samples.create_form_for_batch", return_value={"batch": "form"})
    @patch("core.views.core.utils.samples.get_sample_pre_recorded", return_value=["S1"])
    @patch("core.views.core.utils.samples.check_if_empty_data", return_value=False)
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_form_define_batch_empty_keeps_batch_form(
        self, _schema, _empty, _pre_recorded, _batch_form, render
    ):
        request = self.factory.post("/metadataForm", {"action": "defineBatch"})
        request.user = self.user

        core.views.metadata_form(request)

        render.assert_called_once_with(
            request,
            "core/metadataForm.html",
            {"m_batch_form": {"batch": "form"}, "sample_saved": ["S1"]},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.samples.delete_temporary_sample_table")
    @patch("core.views.core.utils.samples.write_form_data_to_excel")
    @patch("core.views.core.utils.samples.join_sample_and_batch", return_value={"sample": "data"})
    @patch("core.views.core.utils.samples.check_if_empty_data", return_value=True)
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_form_define_batch_success_writes_and_cleans_temp_data(
        self,
        _schema,
        _empty,
        join_data,
        write_excel,
        delete_temp,
        render,
    ):
        request = self.factory.post("/metadataForm", {"action": "defineBatch"})
        request.user = self.user

        core.views.metadata_form(request)

        join_data.assert_called_once()
        write_excel.assert_called_once_with({"sample": "data"}, self.user)
        delete_temp.assert_called_once_with(self.user)
        render.assert_called_once_with(
            request,
            "core/metadataForm.html",
            {"sample_recorded": {"ok": "OK"}},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.samples.create_form_for_batch", return_value={"batch": "form"})
    @patch("core.views.core.utils.samples.get_sample_pre_recorded", return_value=["S1"])
    @patch("core.views.core.utils.samples.pending_samples_in_metadata_form", return_value=True)
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_form_get_resumes_pending_batch(
        self, _schema, _pending, _pre_recorded, _batch_form, render
    ):
        request = self.factory.get("/metadataForm")
        request.user = self.user

        core.views.metadata_form(request)

        render.assert_called_once_with(
            request,
            "core/metadataForm.html",
            {"m_batch_form": {"batch": "form"}, "sample_saved": ["S1"]},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.samples.create_metadata_form", return_value={"ERROR": "No schema"})
    @patch("core.views.core.utils.samples.pending_samples_in_metadata_form", return_value=False)
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_form_get_renders_form_error(
        self, _schema, _pending, _form, render
    ):
        request = self.factory.get("/metadataForm")
        request.user = self.user

        core.views.metadata_form(request)

        render.assert_called_once_with(
            request,
            "core/metadataForm.html",
            {"ERROR": "No schema"},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.samples.create_metadata_form", return_value={"lab_name": ""})
    @patch("core.views.core.utils.samples.pending_samples_in_metadata_form", return_value=False)
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_form_get_requires_assigned_lab(
        self, _schema, _pending, _form, render
    ):
        request = self.factory.get("/metadataForm")
        request.user = self.user

        core.views.metadata_form(request)

        render.assert_called_once_with(
            request,
            "core/metadataForm.html",
            {"ERROR": core.config.ERROR_USER_IS_NOT_ASSIGNED_TO_LAB},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.samples.create_metadata_form", return_value={"lab_name": "Lab A"})
    @patch("core.views.core.utils.samples.pending_samples_in_metadata_form", return_value=False)
    @patch("core.views.core.utils.schema.get_latest_schema", return_value=object())
    def test_metadata_form_get_renders_metadata_form(
        self, _schema, _pending, _form, render
    ):
        request = self.factory.get("/metadataForm")
        request.user = self.user

        core.views.metadata_form(request)

        render.assert_called_once_with(
            request,
            "core/metadataForm.html",
            {"m_form": {"lab_name": "Lab A"}},
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.labs.get_lab_name_from_user", return_value="Lab A")
    @patch(
        "core.views.core.utils.labs.get_lab_contact_details",
        return_value={"ERROR": "Missing contact"},
    )
    def test_laboratory_contact_renders_missing_contact_error(
        self, _contact, _lab_name, render
    ):
        request = self.factory.get("/laboratoryContact")
        request.user = self.user

        core.views.laboratory_contact(request)

        render.assert_called_once_with(
            request,
            "core/laboratoryContact.html",
            {
                "ERROR": "Missing contact : No contact data found for your laboratory Lab A",
                "lab_data": {"error": "Missing contact"},
            },
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.labs.update_contact_lab", return_value={"ERROR": "Invalid phone"})
    @patch("core.views.core.utils.labs.get_lab_name_from_user", return_value="Lab A")
    @patch(
        "core.views.core.utils.labs.get_lab_contact_details",
        return_value={"Phone Number": "123", "Email": "old@example.org"},
    )
    def test_laboratory_contact_update_error(self, _contact, _lab_name, _update, render):
        request = self.factory.post(
            "/laboratoryContact",
            {"action": "updateLabData", "phone_number": ""},
        )
        request.user = self.user

        core.views.laboratory_contact(request)

        render.assert_called_once_with(
            request,
            "core/laboratoryContact.html",
            {
                "ERROR": "Invalid phone - Could not update your contact details",
                "lab_data": {"phone_number": "123", "email": "old@example.org"},
            },
        )

    @patch("core.views.render")
    @patch("core.views.core.utils.labs.update_contact_lab", return_value=True)
    @patch("core.views.core.utils.labs.get_lab_name_from_user", return_value="Lab A")
    @patch(
        "core.views.core.utils.labs.get_lab_contact_details",
        return_value={"Phone Number": "123", "Email": "old@example.org"},
    )
    def test_laboratory_contact_update_success_merges_posted_values(
        self, _contact, _lab_name, _update, render
    ):
        request = self.factory.post(
            "/laboratoryContact",
            {
                "action": "updateLabData",
                "phone_number": "456",
                "email": "",
            },
        )
        request.user = self.user

        core.views.laboratory_contact(request)

        render.assert_called_once_with(
            request,
            "core/laboratoryContact.html",
            {
                "Success": "Success",
                "lab_data": {"phone_number": "456", "email": "old@example.org"},
            },
        )

    @patch("core.views.render")
    def test_contact_renders_static_contact_information(self, render):
        request = self.factory.get("/Contact")

        core.views.contact(request)

        render.assert_called_once_with(
            request,
            "core/contact.html",
            {
                "contact_data": {
                    "email": "bioinformatica@isciii.es",
                    "telephone": "(+34) 91 822 37 95",
                }
            },
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.annotation.check_if_annotation_exists",
        return_value=False,
    )
    def test_annotation_display_renders_not_found_for_unknown_annotation(
        self,
        _exists,
        render,
    ):
        request = self.factory.get("/annotationDisplay=999")
        request.user = self.admin

        core.views.annotation_display(request, 999)

        render.assert_called_once_with(request, "core/error_404.html")

    @patch("core.views.redirect")
    def test_annotation_display_redirects_non_admin_user(self, redirect):
        request = self.factory.get("/annotationDisplay=1")
        request.user = self.user

        core.views.annotation_display(request, 1)

        redirect.assert_called_once_with("/")

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.annotation.get_annotation_data",
        return_value={"organism": "NC_045512"},
    )
    @patch(
        "core.views.core.utils.annotation.check_if_annotation_exists",
        return_value=True,
    )
    def test_annotation_display_renders_existing_annotation(
        self,
        _exists,
        _annotation_data,
        render,
    ):
        request = self.factory.get("/annotationDisplay=1")
        request.user = self.admin

        core.views.annotation_display(request, 1)

        render.assert_called_once_with(
            request,
            "core/annotationDisplay.html",
            {"annotation_data": {"organism": "NC_045512"}},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.annotation.get_annotations",
        return_value=[[1, "NC_045512"]],
    )
    def test_organism_annotation_get_renders_loaded_annotations(
        self,
        _annotations,
        render,
    ):
        request = self.factory.get("/organismAnnotation")
        request.user = self.admin

        core.views.organism_annotation(request)

        render.assert_called_once_with(
            request,
            "core/organismAnnotation.html",
            {"annotations": [[1, "NC_045512"]]},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.annotation.read_gff_file",
        return_value={"ERROR": "Duplicate organism"},
    )
    @patch(
        "core.views.core.utils.annotation.get_annotations",
        return_value=[],
    )
    def test_organism_annotation_propagates_upload_error(
        self,
        _annotations,
        _read_gff,
        render,
    ):
        request = self.factory.post(
            "/organismAnnotation",
            {"action": "uploadAnnotation"},
        )
        request.user = self.admin
        request.FILES["gffFile"] = MagicMock()

        core.views.organism_annotation(request)

        render.assert_called_once_with(
            request,
            "core/organismAnnotation.html",
            {"ERROR": "Duplicate organism", "annotations": []},
        )

    @patch("core.views.render")
    @patch(
        "core.views.core.utils.samples_graphics.received_per_lab",
        return_value="lab graph",
    )
    @patch(
        "core.views.core.utils.samples_graphics.received_per_ccaa",
        return_value="ccaa graph",
    )
    @patch(
        "core.views.core.utils.samples_graphics.received_samples_graph",
        return_value="timeline",
    )
    @patch(
        "core.views.core.utils.samples_map.create_samples_received_map",
        return_value="map",
    )
    def test_received_samples_composes_all_graphics(
        self,
        _map,
        _timeline,
        _ccaa,
        _lab,
        render,
    ):
        request = self.factory.get("/receivedSamples")
        request.user = self.user

        core.views.received_samples(request)

        render.assert_called_once_with(
            request,
            "core/receivedSamples.html",
            {
                "sample_data": {
                    "map": "map",
                    "received_samples_graph": "timeline",
                    "samples_per_ccaa": "ccaa graph",
                    "samples_per_lab": "lab graph",
                }
            },
        )
