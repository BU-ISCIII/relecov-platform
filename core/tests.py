import json
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.test import RequestFactory, SimpleTestCase, TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

import core.api.utils.samples
import core.api.views
import core.models
import core.utils.generic_functions
import core.utils.lab_catalog
import core.utils.lineage
import core.utils.samples
from core.views import (
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
