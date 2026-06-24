from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import plotly.graph_objects as go
from django.test import RequestFactory, SimpleTestCase, TestCase

import core.config
import core.utils.plotly_graphics
import dashboard.models
import dashboard.utils.generic_graphic_data
import dashboard.utils.generic_process_data
import dashboard.utils.met_bioinfo
import dashboard.utils.met_host_info
import dashboard.utils.met_index
import dashboard.utils.met_sample_preprocessing
import dashboard.utils.met_sequencing
import dashboard.utils.plotly
import dashboard.utils.var_lineage_variation_over_time_graph
import dashboard.utils.var_needle_mutation_graph_by_lineage
import dashboard.views


class DashboardDataPreparationTests(SimpleTestCase):
    def test_empty_category_keys_are_merged_under_placeholder(self):
        result = dashboard.utils.generic_process_data.normalize_empty_keys(
            {
                None: {"2026-W01": 2},
                "": {"2026-W01": 3, "2026-W02": 1},
                "Hospital A": {"2026-W01": 4},
            }
        )

        self.assertEqual(
            result,
            {
                "Not Provided": {"2026-W01": 5, "2026-W02": 1},
                "Hospital A": {"2026-W01": 4},
            },
        )

    def test_lineage_preparation_fills_missing_weeks_with_zero(self):
        source = pd.DataFrame(
            {
                "Lineage": ["XFG.3", "XFG.3", "JN.1"],
                "Collection date": pd.to_datetime(
                    ["2026-01-05", "2026-01-19", "2026-01-12"]
                ),
                "samples": [2, 3, 4],
            }
        )

        result = dashboard.utils.var_lineage_variation_over_time_graph.prepare_variant_graphic_dataframe(
            source
        )

        xfg_middle_week = result[
            (result["Lineage"] == "XFG.3")
            & (result["Collection date"] == pd.Timestamp("2026-01-12"))
        ]
        self.assertEqual(len(result), 6)
        self.assertEqual(xfg_middle_week.iloc[0]["samples"], 0)

    def test_empty_date_range_returns_explanatory_figure(self):
        data = pd.DataFrame(
            {
                "Lineage": ["XFG.3"],
                "Collection date": pd.to_datetime(["2026-01-05"]),
                "samples": [1],
            }
        )

        figure = dashboard.utils.var_lineage_variation_over_time_graph.build_lineage_variation_figure(
            data,
            start_date="2027-01-01",
            end_date="2027-02-01",
        )

        self.assertEqual(
            figure.layout.annotations[0].text,
            "No samples found for the selected dates",
        )

    def test_lineage_figure_contains_sample_total_and_percentage_traces(self):
        data = pd.DataFrame(
            {
                "Lineage": ["XFG.3", "JN.1", "XFG.3", "JN.1"],
                "Collection date": pd.to_datetime(
                    ["2026-01-05", "2026-01-05", "2026-01-12", "2026-01-12"]
                ),
                "samples": [3, 1, 1, 3],
            }
        )

        figure = dashboard.utils.var_lineage_variation_over_time_graph.build_lineage_variation_figure(
            data,
            start_date="2026-01-01",
            end_date="2026-01-20",
        )

        self.assertEqual(
            [trace.name for trace in figure.data],
            ["Number of samples", "XFG.3", "JN.1"],
        )
        self.assertEqual(list(figure.data[0].y), [4, 4])
        self.assertEqual(list(figure.data[1].y), [75.0, 25.0])

    def test_lineage_figure_accepts_manually_entered_us_dates(self):
        data = pd.DataFrame(
            {
                "Lineage": ["XFG.3", "XFG.3"],
                "Collection date": pd.to_datetime(["2026-01-05", "2026-01-12"]),
                "samples": [2, 5],
            }
        )

        figure = dashboard.utils.var_lineage_variation_over_time_graph.build_lineage_variation_figure(
            data,
            start_date="01/12/2026",
            end_date="01/12/2026",
        )

        self.assertEqual(list(figure.data[0].y), [5])

    def test_lineage_figure_empty_dates_use_full_range(self):
        data = pd.DataFrame(
            {
                "Lineage": ["XFG.3", "XFG.3"],
                "Collection date": pd.to_datetime(["2026-01-05", "2026-01-12"]),
                "samples": [2, 5],
            }
        )

        figure = dashboard.utils.var_lineage_variation_over_time_graph.build_lineage_variation_figure(
            data,
            start_date=None,
            end_date=None,
        )

        self.assertEqual(list(figure.data[0].y), [2, 5])

class GenericProcessDataTests(SimpleTestCase):
    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch("dashboard.utils.generic_process_data.core.utils.rest_api.get_stats_data")
    def test_simple_lims_counts_normalizes_empty_keys_and_caches_result(
        self, get_stats, create_cache
    ):
        get_stats.return_value = {"": 2, None: 3, "Illumina": 4}

        result = (
            dashboard.utils.generic_process_data._pre_proc_simple_lims_counts(
                "instrument", "sequencing_instrument", empty_label="Not Provided"
            )
        )

        self.assertEqual(result, {"SUCCESS": "Success"})
        create_cache.assert_called_once_with(
            {
                "graphic_name": "instrument",
                "graphic_data": {"Not Provided": 5, "Illumina": 4},
            }
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.get_stats_data",
        return_value={"ERROR": "iSkyLIMS unavailable"},
    )
    def test_simple_lims_counts_returns_external_error_without_caching(
        self, _get_stats, create_cache
    ):
        result = (
            dashboard.utils.generic_process_data._pre_proc_simple_lims_counts(
                "instrument", "sequencing_instrument"
            )
        )

        self.assertEqual(result, {"ERROR": "iSkyLIMS unavailable"})
        create_cache.assert_not_called()

    @patch(
        "dashboard.utils.generic_process_data._pre_proc_simple_lims_counts",
        return_value={"SUCCESS": "Success"},
    )
    def test_methodology_lims_count_wrappers_use_expected_fields(self, preprocess):
        functions = [
            (
                dashboard.utils.generic_process_data.pre_proc_nucleic_acid_extraction_protocol,
                (
                    "nucleic_acid_extraction_protocol",
                    "nucleic_acid_extraction_protocol",
                ),
                {"empty_label": "Not Provided"},
            ),
            (
                dashboard.utils.generic_process_data.pre_proc_sequencing_instrument_platform,
                (
                    "sequencing_instrument_platform",
                    "sequencing_instrument_platform",
                ),
                {"empty_label": "Not Provided"},
            ),
            (
                dashboard.utils.generic_process_data.pre_proc_sequencing_instrument_model,
                (
                    "sequencing_instrument_model",
                    "sequencing_instrument_model",
                ),
                {"empty_label": "Not Provided"},
            ),
            (
                dashboard.utils.generic_process_data.pre_proc_library_preparation_kit,
                ("library_preparation_kit", "library_preparation_kit"),
                {"empty_label": "Not Applicable"},
            ),
            (
                dashboard.utils.generic_process_data.pre_proc_read_length,
                ("read_length", "read_length"),
                {},
            ),
        ]

        for function, args, kwargs in functions:
            with self.subTest(function=function.__name__):
                function()
                preprocess.assert_called_with(*args, **kwargs)

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch("dashboard.utils.generic_process_data.core.utils.rest_api.get_stats_data")
    def test_pcr_preprocessing_functions_cache_cleaned_or_raw_lims_data(
        self, get_stats, create_cache
    ):
        get_stats.side_effect = [
            {"": {"20": 1}, "Swab": {"22": 2}},
            {None: {"18": 3}, "Protocol A": {"19": 4}},
            {"Kit A": {"20": 5}},
        ]

        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_specimen_source_pcr_1(),
            {"SUCCESS": "Success"},
        )
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_extraction_protocol_pcr_1(),
            {"SUCCESS": "Success"},
        )
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_library_kit_pcr_1(),
            {"SUCCESS": "Success"},
        )

        payloads = [call.args[0] for call in create_cache.call_args_list]
        self.assertEqual(
            payloads[0],
            {
                "graphic_name": "specimen_source_pcr_1",
                "graphic_data": {"Not Provided": {"20": 1}, "Swab": {"22": 2}},
            },
        )
        self.assertEqual(
            payloads[1],
            {
                "graphic_name": "extraction_protocol_pcr_1",
                "graphic_data": {
                    "Not Provided": {"18": 3},
                    "Protocol A": {"19": 4},
                },
            },
        )
        self.assertEqual(
            payloads[2],
            {
                "graphic_name": "library_kit_pcr_1",
                "graphic_data": {"Kit A": {"20": 5}},
            },
        )

    @patch("dashboard.utils.generic_process_data.core.utils.rest_api.get_stats_data")
    def test_pcr_preprocessing_functions_return_lims_errors(self, get_stats):
        get_stats.return_value = {"ERROR": "iSkyLIMS unavailable"}

        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_specimen_source_pcr_1(),
            {"ERROR": "iSkyLIMS unavailable"},
        )
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_extraction_protocol_pcr_1(),
            {"ERROR": "iSkyLIMS unavailable"},
        )
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_library_kit_pcr_1(),
            {"ERROR": "iSkyLIMS unavailable"},
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.models.Sample.objects.filter"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.models.LineageValues.objects.filter"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.fetch_samples_on_condition"
    )
    def test_variant_graphic_groups_collection_dates_and_filters_rare_variants(
        self,
        fetch_samples,
        filter_lineages,
        filter_samples,
        create_cache,
    ):
        fetch_samples.return_value = {
            "data": [
                {"Sample Name": "S1", "collection_sample_date": "2024-01-01"},
                {"Sample Name": "S2", "collection_sample_date": "2024-01-01"},
                {"Sample Name": "S3", "collection_sample_date": None},
            ]
        }
        lineage_query = MagicMock()
        lineage_query.exclude.return_value.values_list.return_value.distinct.return_value = [
            "Variant A",
            None,
        ]
        filter_lineages.return_value = lineage_query

        sample_query = MagicMock()
        sample_query.values.return_value.annotate.side_effect = [
            [{"lineage_values__value": "Variant A", "count": 10}],
            [],
        ]
        filter_samples.return_value = sample_query

        result = dashboard.utils.generic_process_data.pre_proc_variant_graphic()

        self.assertEqual(result, {"SUCCESS": "Success"})
        self.assertEqual(
            create_cache.call_args.args[0],
            {
                "graphic_name": "variant_graphic_data",
                "graphic_data": {
                    "Collection date": ["2024-01-01"],
                    "Lineage": ["Variant A"],
                    "samples": [10],
                },
            },
        )

    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.fetch_samples_on_condition",
        return_value={"ERROR": "iSkyLIMS unavailable"},
    )
    def test_variant_graphic_returns_lims_error(self, _fetch_samples):
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_variant_graphic(),
            {"ERROR": "iSkyLIMS unavailable"},
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.models.BioinfoAnalysisValue.objects.filter"
    )
    def test_depth_variants_ignores_invalid_values_and_groups_valid_rows(
        self, filter_values, create_cache
    ):
        depth_query = MagicMock()
        depth_query.values.return_value = [
            {"sample__sample_fingerprint": "S1", "value": "10.5"},
            {"sample__sample_fingerprint": "S2", "value": "Not Provided"},
        ]
        variant_query = MagicMock()
        variant_query.values.return_value = [
            {"sample__sample_fingerprint": "S1", "value": "3"},
            {"sample__sample_fingerprint": "S1", "value": None},
            {"sample__sample_fingerprint": "S2", "value": "4"},
        ]
        filter_values.side_effect = [depth_query, variant_query]

        result = dashboard.utils.generic_process_data.pre_proc_depth_variants()

        self.assertEqual(result, {"SUCCESS": "Success"})
        create_cache.assert_called_once_with(
            {
                "graphic_name": "depth_variant_consensus",
                "graphic_data": {10.5: [3]},
            }
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.get_sample_parameter_data"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.models.BioinfoAnalysisValue.objects.filter"
    )
    def test_depth_sample_run_groups_valid_lims_values(
        self, filter_values, get_parameters, create_cache
    ):
        query = MagicMock()
        query.values.return_value = [
            {"sample__sample_unique_id": "S1", "value": "20"},
            {"sample__sample_unique_id": "S2", "value": "bad"},
        ]
        filter_values.return_value = query
        get_parameters.return_value = [
            {"Sample name": "S1", "number_of_samples_in_run": "12"},
            {"Sample name": "S2", "number_of_samples_in_run": "invalid"},
            {"Sample name": "missing", "number_of_samples_in_run": "3"},
        ]

        result = dashboard.utils.generic_process_data.pre_proc_depth_sample_run()

        self.assertEqual(result, {"SUCCESS": "Success"})
        create_cache.assert_called_once_with(
            {
                "graphic_name": "depth_samples_in_run",
                "graphic_data": {20.0: [12]},
            }
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.models.BioinfoAnalysisValue.objects.filter"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.get_sample_parameter_data"
    )
    def test_based_pairs_sequenced_uses_latest_valid_reads_per_sample(
        self, get_parameters, filter_values, create_cache
    ):
        get_parameters.return_value = [
            {"Sample name": "S1", "diagnostic_pcr_Ct_value_1": "22.5"},
            {"Sample name": "S2", "diagnostic_pcr_Ct_value_1": "30"},
            {"Sample name": "S3", "diagnostic_pcr_Ct_value_1": "bad"},
        ]
        values_query = MagicMock()
        values_query.values_list.return_value.order_by.return_value = [
            ("S1", "1000", 3),
            ("S1", "900", 2),
            ("S2", "invalid", 1),
            ("S3", "500", 4),
        ]
        filter_values.return_value = values_query

        result = dashboard.utils.generic_process_data.pre_proc_based_pairs_sequenced()

        self.assertEqual(result, {"SUCCESS": "Success"})
        create_cache.assert_called_once_with(
            {
                "graphic_name": "ct_number_of_base_pairs_sequenced",
                "graphic_data": {1000: [22.5]},
            }
        )

    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.get_sample_parameter_data",
        return_value={"ERROR": "iSkyLIMS unavailable"},
    )
    def test_based_pairs_sequenced_returns_lims_error(self, _get_parameters):
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_based_pairs_sequenced(),
            {"ERROR": "iSkyLIMS unavailable"},
        )

    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.get_sample_parameter_data"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.models.BioinfoAnalysisValue.objects.filter"
    )
    def test_depth_sample_run_handles_empty_database_and_lims_error(
        self, filter_values, get_parameters
    ):
        empty_query = MagicMock()
        empty_query.values.return_value = []
        filter_values.return_value = empty_query
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_depth_sample_run(),
            {"ERROR": "No data"},
        )

        populated_query = MagicMock()
        populated_query.values.return_value = [
            {"sample__sample_unique_id": "S1", "value": "20"}
        ]
        filter_values.return_value = populated_query
        get_parameters.return_value = {"ERROR": "iSkyLIMS unavailable"}
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_depth_sample_run(),
            {"ERROR": "iSkyLIMS unavailable"},
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.models.BioinfoAnalysisValue.objects.filter"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.models.BioinfoAnalysisField.objects.filter"
    )
    def test_bioinfo_percentage_data_clamps_and_filters_values(
        self, filter_fields, filter_values, create_cache
    ):
        filter_fields.return_value = [
            SimpleNamespace(property_name="per_Ns", label_name="Ns"),
            SimpleNamespace(property_name="per_reads_host", label_name="Host"),
        ]
        query = MagicMock()
        query.values_list.return_value = [
            ("per_Ns", "-2"),
            ("per_Ns", "12,5"),
            ("per_Ns", "invalid"),
            ("per_reads_host", "101"),
        ]
        filter_values.return_value = query

        result = dashboard.utils.generic_process_data.pre_proc_bioinfo_percentage_data()

        self.assertEqual(result, {"SUCCESS": "Success"})
        cached = create_cache.call_args.args[0]["graphic_data"]
        self.assertEqual(cached["Ns"], [0.0, 12.5])
        self.assertEqual(cached["Host"], [])

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch("dashboard.utils.generic_process_data.json.load")
    @patch("builtins.open", new_callable=mock_open)
    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.get_summarize_data"
    )
    def test_samples_received_map_matches_regions_and_defaults_missing_counts(
        self, summarize, _open, load_json, create_cache
    ):
        summarize.return_value = {"region": {"Madrid": 7}}
        load_json.return_value = {
            "features": [
                {"properties": {"name": "Madrid", "cartodb_id": 1}},
                {"properties": {"name": "Canarias", "cartodb_id": 2}},
            ]
        }

        result = dashboard.utils.generic_process_data.pre_proc_samples_received_map()

        self.assertEqual(result, {"SUCCESS": "Success"})
        self.assertEqual(
            create_cache.call_args.args[0]["graphic_data"],
            {
                "ccaa_id": [1, 2],
                "ccaa_name": ["Madrid", "Canarias"],
                "samples": [7, "0"],
            },
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch("dashboard.utils.generic_process_data.core.utils.rest_api.get_stats_data")
    def test_host_info_combines_gender_and_age_sources(self, get_stats, create_cache):
        get_stats.side_effect = [
            {"Male": 2, "": 1},
            {"Male": {"20": 2}, "": {"30": 1}},
            {"Male": {"12": 1}, "": {"24": 1}},
            {"20": 2, "-5": 1},
            {"12": 1, "invalid": 3},
        ]

        result = dashboard.utils.generic_process_data.pre_proc_host_info()

        self.assertEqual(result, {"SUCCESS": "Success"})
        cached = create_cache.call_args.args[0]["graphic_data"]
        self.assertEqual(cached["gender_values"], [2, 1])
        self.assertIn("Not Provided", cached["gender_data"])
        self.assertEqual(cached["invalid_data"]["invalid_age_data"], 1)

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.fetch_samples_on_condition"
    )
    def test_samples_per_date_fills_missing_weeks(self, fetch_samples, create_cache):
        fetch_samples.return_value = {
            "data": [
                {"Sample Name": "S1", "collection_sample_date": "2024-01-01"},
                {"Sample Name": "S2", "collection_sample_date": "2024-01-15"},
                {"Sample Name": "S3", "collection_sample_date": None},
            ]
        }

        result = dashboard.utils.generic_process_data.pre_proc_samples_per_date_all_lab()

        self.assertEqual(result, {"SUCCESS": "Success"})
        self.assertEqual(
            create_cache.call_args.args[0]["graphic_data"],
            {
                "2024-W01": 1,
                "2024-W02": 0,
                "2024-W03": 1,
            },
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.get_summarize_data"
    )
    def test_received_sample_summaries_cache_laboratory_and_region_axes(
        self, summarize, create_cache
    ):
        summarize.return_value = {
            "laboratory": {"Lab A": 2},
            "region": {"Madrid": 3},
        }

        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_samples_received_per_lab(),
            {"SUCCESS": "Success"},
        )
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_samples_received_per_ccaa(),
            {"SUCCESS": "Success"},
        )

        payloads = [call.args[0] for call in create_cache.call_args_list]
        self.assertEqual(payloads[0]["graphic_data"], {"x": ["Lab A"], "y": [2]})
        self.assertEqual(payloads[1]["graphic_data"], {"x": ["Madrid"], "y": [3]})

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.public_db.get_public_accession_from_sample_lab"
    )
    def test_public_accessions_are_grouped_by_laboratory(
        self, get_accessions, create_cache
    ):
        get_accessions.side_effect = [
            [("Lab A", "G1", "S1"), ("Lab A", "G2", "S2")],
            [("Lab B", "E1", "S3")],
        ]

        dashboard.utils.generic_process_data.pre_proc_intranet_gisaid_data()
        dashboard.utils.generic_process_data.pre_proc_intranet_ena_data()

        payloads = [call.args[0] for call in create_cache.call_args_list]
        self.assertEqual(
            payloads[0]["graphic_data"]["Lab A"],
            [("G1", "S1"), ("G2", "S2")],
        )
        self.assertEqual(payloads[1]["graphic_data"]["Lab B"], [("E1", "S3")])

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.get_sample_project_field_display_map",
        return_value={"field_a": "Field A"},
    )
    @patch("dashboard.utils.generic_process_data.core.utils.rest_api.get_stats_data")
    def test_methodology_lims_utilization_builds_summary_and_detail(
        self, get_stats, _display_map, create_cache
    ):
        get_stats.return_value = {
            "fields_norm": {"field_a": 0.5, "field_b": 1.0},
            "always_none": ["field_c"],
            "never_used": ["field_d"],
            "fields_value": {"field_a": 2, "field_b": 4},
        }

        result = (
            dashboard.utils.generic_process_data.pre_proc_methodology_lims_fields_util()
        )

        self.assertEqual(result, {"SUCCESS": "Success"})
        cached = create_cache.call_args.args[0]["graphic_data"]
        self.assertEqual(cached["lims_f_values"], 75.0)
        self.assertEqual(cached["summary_lab_values"], [2, 4])
        self.assertEqual(
            cached["field_detail_data"]["field_name"],
            ["Field A", "field_b"],
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.bioinfo_analysis.get_bioinfo_analysis_fields_utilization",
        return_value={"fields_value": {"field": 2}},
    )
    def test_bioinfo_utilization_is_cached_without_using_stale_cache(
        self, utilization, create_cache
    ):
        result = dashboard.utils.generic_process_data.pre_proc_bioinfo_fields_util()

        self.assertEqual(result, {"SUCCESS": "Success"})
        utilization.assert_called_once_with(use_cache=False)
        create_cache.assert_called_once_with(
            {
                "graphic_name": "methodology_bioinfo_fields",
                "graphic_data": {"fields_value": {"field": 2}},
            }
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch("dashboard.utils.generic_process_data.core.utils.rest_api.get_sample_parameter_data")
    @patch("dashboard.utils.generic_process_data.core.models.Sample.objects.all")
    @patch(
        "dashboard.utils.generic_process_data.core.models.BioinfoAnalysisValue.objects.filter"
    )
    def test_calculation_date_caches_valid_step_durations_only(
        self, analysis_filter, sample_all, get_parameter_data, create_cache
    ):
        analysis_filter.return_value.values.return_value = [
            {"sample__sample_unique_id": "S1", "value": "2024-01-10"},
            {"sample__sample_unique_id": "S2", "value": "2018-01-01"},
            {"sample__sample_unique_id": "S3", "value": "Not Provided"},
        ]
        sample_all.return_value.values.return_value = [
            {
                "sample_unique_id": "S1",
                "sequencing_date": datetime(2024, 1, 5),
            },
            {
                "sample_unique_id": "S2",
                "sequencing_date": datetime(2024, 1, 5),
            },
            {
                "sample_unique_id": "S3",
                "sequencing_date": datetime(2024, 1, 5),
            },
        ]
        get_parameter_data.side_effect = [
            [
                {"Sample Name": "S1", "collection_sample_date": "2024-01-01"},
                {"Sample Name": "S2", "collection_sample_date": "2024-01-01"},
                {"Sample Name": "S3", "collection_sample_date": "Not Provided"},
            ],
            [
                {"Sample Name": "S1", "sample_entry_date": "2024-01-08"},
                {"Sample Name": "S2", "sample_entry_date": "2024-01-08"},
                {"Sample Name": "S3", "sample_entry_date": "2024-01-08"},
            ],
        ]

        result = dashboard.utils.generic_process_data.pre_proc_calculation_date()

        self.assertEqual(result, {"SUCCESS": "Success"})
        self.assertEqual(
            create_cache.call_args.args[0],
            {
                "graphic_name": "calculation_date",
                "graphic_data": {
                    "Collection to sequencing": [4],
                    "Sequencing to analysis": [5],
                    "Sequencing to DB recording": [3, 3],
                },
            },
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch(
        "dashboard.utils.generic_process_data.Prefetch",
        side_effect=lambda *args, **kwargs: ("prefetch", args, kwargs),
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.variants.get_domains_and_coordenates",
        return_value=[{"start": 1, "end": 10}],
    )
    @patch(
        "dashboard.utils.generic_process_data.core.models.VariantAnnotation.objects.filter"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.models.VariantInSample.objects.filter"
    )
    @patch("dashboard.utils.generic_process_data.core.models.Sample.objects.prefetch_related")
    @patch(
        "dashboard.utils.generic_process_data.core.models.LineageValues.objects.filter"
    )
    def test_variations_per_lineage_caches_common_variant_positions(
        self,
        lineage_filter,
        prefetch_samples,
        variant_filter,
        annotation_filter,
        _domains,
        _prefetch,
        create_cache,
    ):
        lineage_queryset = MagicMock()
        lineage_queryset.exclude.return_value = lineage_queryset
        lineage_queryset.values_list.return_value.distinct.return_value = ["XFG.3"]
        lineage_filter.return_value = lineage_queryset
        sample_a = SimpleNamespace(
            lineage_values=SimpleNamespace(
                all=lambda: [SimpleNamespace(value="XFG.3")]
            )
        )
        sample_b = SimpleNamespace(
            lineage_values=SimpleNamespace(
                all=lambda: [SimpleNamespace(value="XFG.3")]
            )
        )
        prefetch_samples.return_value = [sample_a, sample_b]
        variants_query = MagicMock()
        variants_query.values_list.return_value.distinct.return_value = [101, 999]
        counts_query = MagicMock()
        counts_query.values.return_value.annotate.return_value.annotate.return_value = [
            {"variantID_id": 101, "sample_count": 2, "pos": 234}
        ]
        variant_filter.side_effect = [variants_query, counts_query]
        annotation_filter.return_value.values_list.return_value.last.return_value = (
            "missense"
        )

        result = dashboard.utils.generic_process_data.pre_proc_variations_per_lineage(
            chromosome="NC_045512"
        )

        self.assertEqual(result, {"SUCCESS": "Success"})
        self.assertEqual(
            create_cache.call_args.args[0],
            {
                "graphic_name": "variations_per_lineage",
                "graphic_data": {
                    "XFG.3": {
                        "x": [234],
                        "y": [1.0],
                        "mutationGroups": ["missense"],
                        "domains": [{"start": 1, "end": 10}],
                        "SamplesWithLineage": 2,
                    }
                },
            },
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch("dashboard.utils.generic_process_data.core.utils.lab_catalog.ensure_lab_display")
    @patch("dashboard.utils.generic_process_data.core.utils.lab_catalog.get_lab_code")
    @patch("dashboard.utils.generic_process_data.core.models.Sample.objects.filter")
    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.fetch_samples_on_condition"
    )
    def test_samples_per_date_detailed_fills_week_range_and_lab_display(
        self, fetch_samples, sample_filter, get_lab_code, ensure_lab_display, create_cache
    ):
        fetch_samples.return_value = {
            "data": [
                {"Sample Name": "S1", "collection_sample_date": datetime(2024, 1, 1)},
                {"Sample Name": "S2", "collection_sample_date": datetime(2024, 1, 15)},
            ]
        }
        get_lab_code.return_value = "LAB-01"
        ensure_lab_display.return_value = "Hospital A"
        relevant_samples = MagicMock()
        sample_filter.return_value.annotate.return_value = relevant_samples
        valid_samples = MagicMock()
        relevant_samples.exclude.return_value = valid_samples
        valid_samples.filter.return_value = valid_samples
        valid_samples.annotate.return_value.values.return_value.order_by.return_value.annotate.return_value = [
            {
                "submitting_institution": "Submitter A",
                "lab_code_1": None,
                "collecting_institution": "Legacy Hospital",
                "iso_yearweek": "2024-W01",
                "num_samples": 1,
            },
            {
                "submitting_institution": "Submitter A",
                "lab_code_1": None,
                "collecting_institution": "Legacy Hospital",
                "iso_yearweek": "2024-W03",
                "num_samples": 2,
            },
        ]

        result = dashboard.utils.generic_process_data.pre_proc_samples_per_date_all_lab(
            detailed=True
        )

        self.assertEqual(result, {"SUCCESS": "Success"})
        self.assertEqual(
            create_cache.call_args.args[0]["graphic_data"],
            [
                {
                    "submitting_institution": "Submitter A",
                    "collecting_institution": "Hospital A",
                    "lab_code_1": "LAB-01",
                    "legacy_collecting_institution": "Legacy Hospital",
                    "iso_yearweek": "2024-W01",
                    "num_samples": 1,
                },
                {
                    "submitting_institution": "Submitter A",
                    "collecting_institution": "Hospital A",
                    "lab_code_1": "LAB-01",
                    "legacy_collecting_institution": "Legacy Hospital",
                    "iso_yearweek": "2024-W02",
                    "num_samples": 0,
                },
                {
                    "submitting_institution": "Submitter A",
                    "collecting_institution": "Hospital A",
                    "lab_code_1": "LAB-01",
                    "legacy_collecting_institution": "Legacy Hospital",
                    "iso_yearweek": "2024-W03",
                    "num_samples": 2,
                },
            ],
        )

    @patch(
        "dashboard.utils.generic_process_data.dashboard.models.GraphicJsonFile.objects.create_new_graphic_json"
    )
    @patch("dashboard.utils.generic_process_data.core.utils.lab_catalog.get_lab_code")
    @patch("dashboard.utils.generic_process_data.core.models.Sample.objects.filter")
    @patch(
        "dashboard.utils.generic_process_data.core.models.LineageValues.objects.filter"
    )
    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.fetch_samples_on_condition"
    )
    def test_search_samples_summary_groups_rows_by_submitter_and_lab(
        self, fetch_samples, lineage_filter, sample_filter, get_lab_code, create_cache
    ):
        fetch_samples.return_value = {
            "data": [
                {"Sample Name": "S1", "collection_sample_date": "2024-01-01"},
                {"Sample Name": "S2", "collection_sample_date": "2024-01-02"},
                {"Sample Name": "MISSING", "collection_sample_date": "2024-01-03"},
            ]
        }
        lineage_filter.return_value.select_related.return_value = object()
        get_lab_code.return_value = "LAB-02"
        sample_with_lineage = SimpleNamespace(
            pk=1,
            sample_unique_id="S1",
            sequencing_sample_id="SEQ-1",
            lab_code_1="LAB-01",
            collecting_institution="Hospital A",
            submitting_institution="Submitter A",
            filt_lineages=[SimpleNamespace(value="XFG.3")],
        )
        sample_without_lineage = SimpleNamespace(
            pk=2,
            sample_unique_id="S2",
            sequencing_sample_id="SEQ-2",
            lab_code_1=None,
            collecting_institution="Hospital B",
            submitting_institution="Submitter A",
            filt_lineages=[],
        )
        sample_filter.return_value.prefetch_related.return_value.order_by.return_value = [
            sample_with_lineage,
            sample_without_lineage,
        ]

        result = dashboard.utils.generic_process_data.pre_proc_search_samples_summary()

        self.assertEqual(result, {"SUCCESS": "Success"})
        self.assertEqual(
            create_cache.call_args.args[0],
            {
                "graphic_name": "search_samples_summary_table",
                "graphic_data": {
                    "Submitter A": {
                        "LAB-01": {
                            "lab_code_1": "LAB-01",
                            "collecting_institution": "Hospital A",
                            "rows": [[1, "SEQ-1", "2024-01-01", "XFG.3", "Hospital A"]],
                        },
                        "LAB-02": {
                            "lab_code_1": "LAB-02",
                            "collecting_institution": "Hospital B",
                            "rows": [
                                [
                                    2,
                                    "SEQ-2",
                                    "2024-01-02",
                                    "Not Defined",
                                    "Hospital B",
                                ]
                            ],
                        },
                    }
                },
            },
        )

    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.get_summarize_data",
        return_value={"ERROR": "iSkyLIMS unavailable"},
    )
    def test_received_sample_summaries_return_lims_errors(self, _summarize):
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_samples_received_per_lab(),
            {"ERROR": "iSkyLIMS unavailable"},
        )
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_samples_received_per_ccaa(),
            {"ERROR": "iSkyLIMS unavailable"},
        )

    @patch(
        "dashboard.utils.generic_process_data.core.utils.rest_api.get_stats_data",
        return_value={"ERROR": "iSkyLIMS unavailable"},
    )
    def test_methodology_lims_utilization_returns_lims_error(self, _get_stats):
        self.assertEqual(
            dashboard.utils.generic_process_data.pre_proc_methodology_lims_fields_util(),
            {"ERROR": "iSkyLIMS unavailable"},
        )


class NeedleMutationGraphTests(SimpleTestCase):
    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.dashboard.utils.generic_process_data.pre_proc_variations_per_lineage",
        return_value={"SUCCESS": "Success"},
    )
    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_variant_data_preprocesses_missing_cache_then_reads_refreshed_data(
        self, get_cache, preprocess
    ):
        get_cache.side_effect = [
            None,
            {
                "BA.2": {"SamplesWithLineage": 1, "x": [10]},
                "XFG.3": {"SamplesWithLineage": 2, "x": [20]},
            },
        ]

        data, lineage, samples = (
            dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages(
                graphic_name="variations_per_lineage",
                chromosome="NC_045512",
            )
        )

        preprocess.assert_called_once_with("NC_045512")
        self.assertEqual(lineage, "BA.2")
        self.assertEqual(samples, 1)
        self.assertEqual(data["x"], [10])

    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.dashboard.utils.generic_process_data.pre_proc_variations_per_lineage",
        return_value={"SUCCESS": "Success"},
    )
    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value=None,
    )
    def test_variant_data_returns_empty_tuple_when_preprocess_does_not_create_cache(
        self, _cache, _preprocess
    ):
        self.assertEqual(
            dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages(
                graphic_name="variations_per_lineage"
            ),
            (None, None, None),
        )

    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages"
    )
    def test_needle_figure_builds_domains_mutation_traces_and_rangeslider(
        self, get_data
    ):
        get_data.return_value = (
            {
                "SamplesWithLineage": 3,
                "x": ["10", "20", "40"],
                "y": [0.2, 0.8, 0.5],
                "mutationGroups": ["missense_variant", None, "unknown_effect"],
                "domains": [
                    {"name": "S", "coord": "1-30"},
                    {"name": "N", "coord": "31-60"},
                ],
            },
            "XFG.3",
            3,
        )

        figure, markdown = (
            dashboard.utils.var_needle_mutation_graph_by_lineage.build_needle_plot_figure(
                "XFG.3",
                toggle_rangeslider=["on"],
                relayout_data={"xaxis.range": [0, 25]},
            )
        )

        self.assertEqual(markdown, "Showing mutations for 3 samples")
        self.assertTrue(figure.layout.xaxis.rangeslider.visible)
        self.assertEqual(list(figure.layout.xaxis.range), [0, 25])
        self.assertEqual(
            [trace.name for trace in figure.data],
            [
                "missense_variant",
                "missense_variant",
                "Unknown",
                "Unknown",
            ],
        )
        self.assertEqual(len(figure.layout.shapes), 3)
        self.assertEqual(figure.layout.updatemenus[0].buttons[0].label, "All")

    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages"
    )
    def test_needle_figure_uses_data_range_when_relayout_is_absent(self, get_data):
        get_data.return_value = (
            {
                "SamplesWithLineage": 1,
                "x": ["50"],
                "y": [0.4],
                "mutationGroups": ["synonymous_variant"],
                "domains": [{"name": "S", "coord": "1-100"}],
            },
            "XFG.3",
            1,
        )

        figure, _markdown = (
            dashboard.utils.var_needle_mutation_graph_by_lineage.build_needle_plot_figure(
                "XFG.3"
            )
        )

        self.assertEqual(list(figure.layout.xaxis.range), [50, 50])
        self.assertEqual(figure.data[1].name, "synonymous_variant")

    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages"
    )
    def test_needle_figure_merges_domain_case_variants(self, get_data):
        get_data.return_value = (
            {
                "SamplesWithLineage": 1,
                "x": ["100"],
                "y": [0.4],
                "mutationGroups": ["synonymous_variant"],
                "domains": [
                    {"name": "orf1ab", "coord": "1-200"},
                    {"name": "ORF1ab", "coord": "1-200"},
                    {"name": "s", "coord": "201-300"},
                    {"name": "S", "coord": "201-300"},
                ],
            },
            "XFG.3",
            1,
        )

        figure, _markdown = (
            dashboard.utils.var_needle_mutation_graph_by_lineage.build_needle_plot_figure(
                "XFG.3"
            )
        )

        button_labels = [
            button.label for button in figure.layout.updatemenus[0].buttons
        ]
        annotation_texts = [
            annotation.text for annotation in figure.layout.annotations
        ]

        self.assertEqual(button_labels, ["All", "ORF1ab", "S"])
        self.assertEqual(annotation_texts.count("ORF1ab"), 1)
        self.assertEqual(annotation_texts.count("S"), 1)
        self.assertNotIn("orf1ab", annotation_texts)
        self.assertNotIn("s", annotation_texts)
        self.assertEqual(figure.layout.shapes[0].fillcolor, "#1f77b4")
        self.assertEqual(figure.layout.shapes[1].fillcolor, "#ff7f0e")

    def test_needle_plot_graph_initial_arguments_handle_empty_and_success(self):
        self.assertEqual(
            dashboard.utils.var_needle_mutation_graph_by_lineage.create_needle_plot_graph_mutation_by_lineage(
                ["XFG.3"],
                "XFG.3",
                None,
                0,
            ),
            {"ERROR": "No lineage mutation data available"},
        )
        self.assertEqual(
            dashboard.utils.var_needle_mutation_graph_by_lineage.create_needle_plot_graph_mutation_by_lineage(
                ["XFG.3"],
                "XFG.3",
                {"x": [1]},
                2,
            ),
            {
                "needleplot-select-lineage": {
                    "options": [{"label": "XFG.3", "value": "XFG.3"}],
                    "value": "XFG.3",
                },
                "toggle-rangeslider": {"value": ["on"]},
            },
        )


class MethodologyDashboardTests(SimpleTestCase):
    @patch("dashboard.utils.met_index.GraphicJsonFile.objects.filter")
    def test_cached_graphic_json_reads_latest_string_payload_or_missing_cache(
        self, graphic_filter
    ):
        graphic_filter.return_value.latest.return_value.graphic_data = '{"value": 3}'

        self.assertEqual(
            dashboard.utils.met_index._read_cached_graphic_json("cached"),
            {"value": 3},
        )

        graphic_filter.return_value.latest.side_effect = (
            dashboard.models.GraphicJsonFile.DoesNotExist
        )
        self.assertIsNone(
            dashboard.utils.met_index._read_cached_graphic_json("missing")
        )

    @patch("dashboard.utils.met_index.core.utils.samples.get_samples_count")
    @patch(
        "dashboard.utils.met_index.core.utils.bioinfo_analysis.get_bioinfo_analysis_fields_utilization"
    )
    @patch(
        "dashboard.utils.met_index.dashboard.utils.generic_process_data.pre_proc_bioinfo_fields_util"
    )
    @patch(
        "dashboard.utils.met_index.dashboard.utils.generic_process_data.pre_proc_methodology_lims_fields_util"
    )
    @patch("dashboard.utils.met_index._read_cached_bioinfo_util")
    @patch("dashboard.utils.met_index._read_cached_lims_util")
    @patch("dashboard.utils.met_index.core.utils.schema.get_default_schema")
    def test_schema_utilization_preprocesses_missing_caches_and_falls_back_to_bioinfo(
        self,
        get_schema,
        read_lims,
        read_bioinfo,
        preproc_lims,
        preproc_bioinfo,
        fallback_bioinfo,
        get_samples_count,
    ):
        get_schema.return_value = object()
        read_lims.side_effect = [
            None,
            {
                "lims_f_values": 40,
                "summary_lab_values": [2, 5],
                "field_detail_data": {
                    "field_name": ["Lab Field"],
                    "field_value": [3],
                    "percent": [5],
                },
                "num_lab_fields": 1,
            },
        ]
        read_bioinfo.return_value = None
        preproc_lims.return_value = {"SUCCESS": "Success"}
        preproc_bioinfo.return_value = {"ERROR": "No cached bioinfo"}
        fallback_bioinfo.return_value = {
            "fields_value": {"Bio Field": 4},
            "always_none": [],
            "never_used": ["Unused"],
            "fields_norm": ["Bio Field"],
        }
        get_samples_count.return_value = 2

        result = dashboard.utils.met_index.schema_fields_utilization()

        self.assertEqual(result["lims_f_values"], 40)
        self.assertEqual(result["bio_f_values"], 200.0)
        self.assertEqual(result["summary"]["lab_values"], [2, 5])
        self.assertEqual(result["summary"]["bio_values"], [1, 2])
        preproc_lims.assert_called_once_with()
        preproc_bioinfo.assert_called_once_with()
        fallback_bioinfo.assert_called_once_with()

    @patch(
        "dashboard.utils.met_index.dashboard.utils.generic_process_data.pre_proc_bioinfo_fields_util",
        return_value={"SUCCESS": "Success"},
    )
    @patch(
        "dashboard.utils.met_index.core.utils.bioinfo_analysis.get_bioinfo_analysis_fields_utilization",
        return_value={},
    )
    @patch(
        "dashboard.utils.met_index.dashboard.utils.generic_process_data.pre_proc_methodology_lims_fields_util",
        return_value={"ERROR": "iSkyLIMS unavailable"},
    )
    @patch("dashboard.utils.met_index._read_cached_bioinfo_util")
    @patch("dashboard.utils.met_index._read_cached_lims_util", return_value=None)
    @patch("dashboard.utils.met_index.core.utils.schema.get_default_schema")
    def test_schema_utilization_reports_lims_error_and_empty_bioinfo_cache(
        self,
        get_schema,
        _read_lims,
        read_bioinfo,
        _preproc_lims,
        _fallback_bioinfo,
        _preproc_bioinfo,
    ):
        get_schema.return_value = object()
        read_bioinfo.side_effect = [None, {}]

        result = dashboard.utils.met_index.schema_fields_utilization()

        self.assertEqual(result["ERROR"], "iSkyLIMS unavailable")
        self.assertEqual(result["ERROR_ANALYSIS"], "Not Data to process")

    @patch("dashboard.utils.met_index.core.utils.schema.get_default_schema")
    def test_schema_utilization_reports_missing_schema(self, get_schema):
        get_schema.return_value = None

        result = dashboard.utils.met_index.schema_fields_utilization()

        self.assertIn("NO_SCHEMA", result)

    @patch("dashboard.utils.met_index.core.utils.samples.get_samples_count")
    @patch("dashboard.utils.met_index._read_cached_bioinfo_util")
    @patch("dashboard.utils.met_index._read_cached_lims_util")
    @patch("dashboard.utils.met_index.core.utils.schema.get_default_schema")
    def test_schema_utilization_calculates_completeness(
        self,
        get_schema,
        read_lims,
        read_bioinfo,
        get_sample_count,
    ):
        get_schema.return_value = object()
        get_sample_count.return_value = 2
        read_lims.return_value = {
            "lims_f_values": 75,
            "summary_lab_values": [1, 4],
            "field_detail_data": {
                "field_name": [],
                "field_value": [],
                "percent": [],
            },
            "num_lab_fields": 4,
        }
        read_bioinfo.return_value = {
            "fields_value": {"field_a": 2, "field_b": 1},
            "always_none": ["field_c"],
            "never_used": [],
            "fields_norm": ["field_a", "field_b"],
        }

        result = dashboard.utils.met_index.schema_fields_utilization()

        self.assertEqual(result["lims_f_values"], 75)
        self.assertEqual(result["bio_f_values"], 75.0)
        self.assertEqual(result["summary"]["bio_values"], [1, 3])

    @patch(
        "dashboard.utils.met_index.dashboard.utils.plotly.progress_bar",
        side_effect=["lims-progress", "bio-progress"],
    )
    @patch(
        "dashboard.utils.met_index.dashboard.utils.plotly.bar_graphic",
        side_effect=["grouped", "detailed"],
    )
    @patch("dashboard.utils.met_index.schema_fields_utilization")
    def test_index_dashboard_builds_complete_graphics(
        self,
        utilization,
        bar,
        progress,
    ):
        utilization.return_value = {
            "summary": {
                "group": ["Empty Fields", "Total Fields"],
                "lab_values": [1, 3],
                "bio_values": [1, 2],
            },
            "lims_f_values": 75,
            "bio_f_values": 50,
            "num_lab_fields": 2,
            "num_bio_fields": 1,
            "field_detail_data": {
                "field_name": ["Lab A", "Lab B", "Bio A"],
                "field_value": [2, 1, 1],
                "percent": [2, 2, 2],
            },
        }

        result = dashboard.utils.met_index.index_dash_fields()

        self.assertEqual(result["grouped_fields"], "grouped")
        self.assertEqual(result["detailed_fields"], "detailed")
        self.assertEqual(result["progress_bars"], ["lims-progress", "bio-progress"])
        self.assertEqual(
            list(result["table"]),
            [("Lab A", 2, 2), ("Lab B", 1, 2), ("Bio A", 1, 2)],
        )
        self.assertEqual(bar.call_count, 2)
        self.assertEqual(progress.call_count, 2)

    @patch("dashboard.utils.met_index.schema_fields_utilization")
    def test_index_dashboard_returns_no_schema_error(self, utilization):
        utilization.return_value = {"NO_SCHEMA": "No schema"}

        self.assertEqual(
            dashboard.utils.met_index.index_dash_fields(),
            {"NO_SCHEMA": "No schema"},
        )

    @patch(
        "dashboard.utils.met_index.dashboard.utils.plotly.bar_graphic",
        return_value="bio-grouped",
    )
    @patch("dashboard.utils.met_index.schema_fields_utilization")
    def test_index_dashboard_renders_bioinfo_when_lims_processing_failed(
        self,
        utilization,
        bar,
    ):
        utilization.return_value = {
            "ERROR": "iSkyLIMS unavailable",
            "summary": {
                "group": ["Empty Fields", "Total Fields"],
                "bio_values": [1, 2],
            },
            "bio_f_values": 50,
            "num_bio_fields": 1,
            "field_detail_data": {
                "field_name": ["Bio A"],
                "field_value": [1],
                "percent": [1],
            },
        }

        result = dashboard.utils.met_index.index_dash_fields()

        self.assertEqual(result["ERROR"], "iSkyLIMS unavailable")
        self.assertEqual(result["grouped_fields"], "bio-grouped")
        self.assertEqual(bar.call_count, 2)

    @patch(
        "dashboard.utils.met_index.dashboard.utils.plotly.progress_bar",
        return_value="lims-progress",
    )
    @patch(
        "dashboard.utils.met_index.dashboard.utils.plotly.bar_graphic",
        return_value="lab-grouped",
    )
    @patch("dashboard.utils.met_index.schema_fields_utilization")
    def test_index_dashboard_handles_missing_bioinfo_analysis(
        self,
        utilization,
        _bar,
        _progress,
    ):
        utilization.return_value = {
            "ERROR_ANALYSIS": "No analysis data",
            "summary": {
                "group": ["Empty Fields", "Total Fields"],
                "lab_values": [1, 3],
            },
            "lims_f_values": 75,
        }

        result = dashboard.utils.met_index.index_dash_fields()

        self.assertEqual(result["grouped_fields"], "lab-grouped")
        self.assertEqual(result["ERROR_ANALYSIS"], "No analysis data")
        self.assertEqual(result["progress_bars"], ["lims-progress"])

    @patch("dashboard.utils.met_index.schema_fields_utilization")
    def test_index_dashboard_returns_errors_when_lims_and_bioinfo_fail(
        self, utilization
    ):
        utilization.return_value = {
            "ERROR": "iSkyLIMS unavailable",
            "ERROR_ANALYSIS": "No analysis data",
        }

        self.assertEqual(
            dashboard.utils.met_index.index_dash_fields(),
            {
                "ERROR": "iSkyLIMS unavailable",
                "ERROR_ANALYSIS": "No analysis data",
            },
        )

    @patch(
        "dashboard.utils.met_index.dashboard.utils.plotly.progress_bar",
        side_effect=["lims-progress", "bio-progress"],
    )
    @patch(
        "dashboard.utils.met_index.dashboard.utils.plotly.bar_graphic",
        side_effect=["grouped", "detailed"],
    )
    @patch("dashboard.utils.met_index.schema_fields_utilization")
    def test_index_dashboard_detailed_fields_allow_missing_lab_field_count(
        self,
        utilization,
        bar,
        progress,
    ):
        utilization.return_value = {
            "summary": {
                "group": ["Empty Fields", "Total Fields"],
                "lab_values": [0, 0],
                "bio_values": [1, 2],
            },
            "lims_f_values": 0,
            "bio_f_values": 50,
            "num_bio_fields": 1,
            "field_detail_data": {
                "field_name": ["Bio A"],
                "field_value": [1],
                "percent": [1],
            },
        }

        result = dashboard.utils.met_index.index_dash_fields()

        self.assertEqual(result["detailed_fields"], "detailed")
        self.assertEqual(bar.call_args_list[-1].kwargs["options"]["colors"], None)
        self.assertEqual(progress.call_count, 2)


class GraphicCacheIntegrationTests(TestCase):
    def test_graphic_cache_returns_latest_stored_payload(self):
        dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
            {"graphic_name": "example", "graphic_data": {"samples": 2}}
        )
        dashboard.models.GraphicJsonFile.objects.create_new_graphic_json(
            {"graphic_name": "example", "graphic_data": {"samples": 4}}
        )

        self.assertEqual(
            dashboard.utils.generic_graphic_data.get_graphic_json_data("example"),
            {"samples": 4},
        )
        self.assertIsNone(
            dashboard.utils.generic_graphic_data.get_graphic_json_data("missing")
        )


class DashboardViewTests(SimpleTestCase):
    def setUp(self):
        self.request = RequestFactory().get("/dashboard/test")

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.var_lineage_variation_over_time_graph.create_lineages_variations_graphic",
        return_value={"OK": True},
    )
    def test_lineages_voc_passes_processed_graphic_to_template(
        self,
        _create_graphic,
        render,
    ):
        dashboard.views.lineages_voc(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/variantLineageVoc.html",
            {"draw_lineages": {"lineage_on_time": {"OK": True}}},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages",
        return_value=(None, None, 0),
    )
    @patch("dashboard.views.core.utils.lineage.get_lineages_list", return_value=[])
    @patch("dashboard.views.core.utils.variants.get_default_chromosome")
    def test_mutations_in_lineage_reports_missing_lineage_data(
        self,
        _chromosome,
        _lineages,
        _variant_data,
        render,
    ):
        dashboard.views.mutations_in_lineage(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/variantMutationsInLineage.html",
            {"ERROR": dashboard.dashboard_config.ERROR_NO_LINEAGES_ARE_DEFINED_YET},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.met_host_info.host_info_graphics",
        return_value={"ERROR": "iSkyLIMS unavailable"},
    )
    def test_methodology_host_view_propagates_processing_error(
        self,
        _host_info,
        render,
    ):
        dashboard.views.methodology_host_info(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/methodologyHostInfo.html",
            {"ERROR": {"ERROR": "iSkyLIMS unavailable"}},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.var_needle_mutation_graph_by_lineage.create_needle_plot_graph_mutation_by_lineage",
        return_value={"ERROR": "Unable to build plot"},
    )
    @patch(
        "dashboard.views.dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages",
        return_value=({"mutation": 1}, "XFG.3", 1),
    )
    @patch(
        "dashboard.views.core.utils.lineage.get_lineages_list",
        return_value=["XFG.3"],
    )
    @patch("dashboard.views.core.utils.variants.get_default_chromosome")
    def test_mutations_in_lineage_propagates_plot_creation_error(
        self,
        _chromosome,
        _lineages,
        _variant_data,
        _create_plot,
        render,
    ):
        dashboard.views.mutations_in_lineage(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/variantMutationsInLineage.html",
            {"ERROR": "Unable to build plot"},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.var_needle_mutation_graph_by_lineage.create_needle_plot_graph_mutation_by_lineage",
        return_value={"lineage": "XFG.3"},
    )
    @patch(
        "dashboard.views.dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages",
        return_value=({"mutation": 1}, "XFG.3", 1),
    )
    @patch(
        "dashboard.views.core.utils.lineage.get_lineages_list",
        return_value=["XFG.3"],
    )
    @patch("dashboard.views.core.utils.variants.get_default_chromosome")
    def test_mutations_in_lineage_renders_successful_plot_arguments(
        self,
        _chromosome,
        _lineages,
        _variant_data,
        _create_plot,
        render,
    ):
        dashboard.views.mutations_in_lineage(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/variantMutationsInLineage.html",
            {"needle_plot_initial_arguments": {"lineage": "XFG.3"}},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.met_sequencing.sequencing_graphics",
        return_value={"instrument": "Illumina"},
    )
    def test_methodology_sequencing_renders_successful_data(
        self,
        _sequencing,
        render,
    ):
        dashboard.views.methodology_sequencing(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/methodologySequencing.html",
            {"sequencing": {"instrument": "Illumina"}},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.met_sample_preprocessing.sample_processing_graphics",
        return_value={"ERROR": "No preprocessing data"},
    )
    def test_methodology_sample_processing_renders_error(
        self,
        _processing,
        render,
    ):
        dashboard.views.methodology_sample_processing(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/methodologySampleProcessing.html",
            {"ERROR": {"ERROR": "No preprocessing data"}},
        )

    @patch("dashboard.views.render")
    def test_variants_index_renders_dashboard_landing_page(self, render):
        dashboard.views.variants_index(self.request)

        render.assert_called_once_with(self.request, "dashboard/variantsIndex.html")

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.met_index.index_dash_fields",
        return_value={"progress": "complete"},
    )
    def test_methodology_index_passes_graphics_to_template(self, _graphics, render):
        dashboard.views.methodology_index(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/methodologyIndex.html",
            {"graphics": {"progress": "complete"}},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.met_sequencing.sequencing_graphics",
        return_value={"ERROR": "No sequencing data"},
    )
    def test_methodology_sequencing_renders_error(self, _sequencing, render):
        dashboard.views.methodology_sequencing(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/methodologySequencing.html",
            {"ERROR": {"ERROR": "No sequencing data"}},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.met_sample_preprocessing.sample_processing_graphics",
        return_value={"protocol": "ARTIC"},
    )
    def test_methodology_sample_processing_renders_success(
        self,
        _processing,
        render,
    ):
        dashboard.views.methodology_sample_processing(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/methodologySampleProcessing.html",
            {"sample_processing": {"protocol": "ARTIC"}},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.dashboard.utils.met_bioinfo.bioinfo_graphics",
        return_value={"pipeline": "viralrecon"},
    )
    def test_methodology_bioinfo_passes_graphics_to_template(self, _bioinfo, render):
        dashboard.views.methodology_bioinfo(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/methodologyBioinfo.html",
            {"bioinfo": {"pipeline": "viralrecon"}},
        )

class LineageGraphicLoadingTests(SimpleTestCase):
    @patch(
        "dashboard.utils.var_lineage_variation_over_time_graph.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value=[
            {
                "Lineage": "XFG.3",
                "Collection date": "2026-01-05",
                "samples": "2",
            },
            {
                "Lineage": "Old",
                "Collection date": "2019-01-01",
                "samples": "9",
            },
        ],
    )
    def test_load_variant_dataframe_normalizes_dates_counts_and_cutoff(
        self,
        _cached_data,
    ):
        result = (
            dashboard.utils.var_lineage_variation_over_time_graph.load_variant_graphic_dataframe()
        )

        self.assertEqual(result["Lineage"].tolist(), ["XFG.3"])
        self.assertEqual(result["samples"].tolist(), [2])
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(result["Collection date"]))

    @patch(
        "dashboard.utils.var_lineage_variation_over_time_graph.dashboard.utils.generic_process_data.pre_proc_variant_graphic",
        return_value={"ERROR": "Unable to preprocess"},
    )
    @patch(
        "dashboard.utils.var_lineage_variation_over_time_graph.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value=None,
    )
    def test_load_variant_dataframe_returns_preprocessing_error(
        self,
        _cached_data,
        _preprocess,
    ):
        result = (
            dashboard.utils.var_lineage_variation_over_time_graph.load_variant_graphic_dataframe()
        )

        self.assertEqual(result, {"ERROR": "Unable to preprocess"})


class PlotlyUtilityBranchTests(SimpleTestCase):
    def test_format_labels_preserves_wraps_and_truncates_labels(self):
        unchanged, unchanged_hover = dashboard.utils.plotly.format_labels(["Short"])
        wrapped, wrapped_hover = dashboard.utils.plotly.format_labels(
            ["Long label with words"],
            wrap=8,
        )
        truncated_word, word_hover = dashboard.utils.plotly.format_labels(
            ["abcdefghijklmnop"],
            truncate=8,
        )
        truncated_phrase, phrase_hover = dashboard.utils.plotly.format_labels(
            ["first middle last"],
            truncate=10,
        )

        self.assertEqual(unchanged, ["Short"])
        self.assertEqual(unchanged_hover, ["Short"])
        self.assertIn("<br>", wrapped[0])
        self.assertEqual(wrapped_hover, ["Long label with words"])
        self.assertEqual(truncated_word, ["abcde..."])
        self.assertEqual(word_hover, ["abcdefghijklmnop"])
        self.assertIn("first...last", truncated_phrase[0])
        self.assertEqual(phrase_hover, ["first middle last"])

    def test_log_scaling_handles_zero_flat_and_large_ratio_data(self):
        flat = go.Figure()
        zeros = go.Figure()
        logarithmic = go.Figure()

        self.assertIs(
            core.utils.plotly_graphics.log_ydata_if_needed(flat, [2, 4]),
            flat,
        )
        self.assertIs(
            core.utils.plotly_graphics.log_ydata_if_needed(zeros, [0, 0]),
            zeros,
        )
        core.utils.plotly_graphics.log_ydata_if_needed(
            logarithmic,
            [0, 1, 1000],
        )

        self.assertIsNone(flat.layout.yaxis.type)
        self.assertIsNone(zeros.layout.yaxis.type)
        self.assertEqual(logarithmic.layout.yaxis.type, "log")
        self.assertEqual(logarithmic.layout.yaxis.dtick, 1)

    def test_sample_variant_initial_arguments_normalize_optional_data(self):
        result = core.utils.plotly_graphics.build_sample_variant_initial_arguments(
            {
                "x": ["10", None, "20"],
                "y": [0.1, 0.2],
                "mutationGroups": ["missense_variant"],
            }
        )

        self.assertEqual(result["mdata-store"]["data"]["x"], [10, 20])
        self.assertEqual(result["mdata-store"]["data"]["domains"], [])
        self.assertEqual(result["toggle-rangeslider"]["value"], ["on"])
        self.assertTrue(result["previous-data"]["data"]["first_load"])

    def test_sample_variant_figure_returns_empty_state_without_mutations(self):
        empty = core.utils.plotly_graphics.build_sample_variant_figure({})
        no_positions = core.utils.plotly_graphics.build_sample_variant_figure(
            {"x": []}
        )

        self.assertEqual(
            empty.layout.title.text,
            "No variants available for the selected sample",
        )
        self.assertEqual(
            no_positions.layout.title.text,
            "No variants available for the selected sample",
        )

    def test_sample_variant_figure_builds_domains_ranges_and_mutation_groups(self):
        figure = core.utils.plotly_graphics.build_sample_variant_figure(
            {
                "x": [100, 200, 300],
                "y": [0.2, 0.8, 0.4],
                "mutationGroups": [
                    "missense_variant",
                    None,
                    "custom_effect",
                ],
                "domains": [
                    {"name": "S", "coord": "50-250"},
                    {"name": "Unknown domain", "coord": "240-400"},
                ],
            },
            toggle_rangeslider=["on"],
            relayout_data={"xaxis.range": [90, 250]},
        )

        self.assertTrue(figure.layout.xaxis.rangeslider.visible)
        self.assertEqual(list(figure.layout.xaxis.range), [90, 250])
        self.assertEqual(
            {trace.name for trace in figure.data},
            {"missense_variant", "Unknown"},
        )
        self.assertEqual(len(figure.layout.updatemenus[0].buttons), 3)
        self.assertGreaterEqual(len(figure.layout.shapes), 3)

    @patch("dashboard.utils.plotly.plot", return_value="<div>plot</div>")
    def test_dashboard_graph_builders_render_expected_plot_divs(self, plot):
        bar = dashboard.utils.plotly.bar_graphic(
            {"group": ["A", "Long hospital name"], "value": [1, 1000]},
            ["group", "value"],
            ["Samples"],
            {"title": "Samples"},
            {
                "title": "Bar",
                "truncate_labels": 10,
                "log_scaling": True,
            },
        )
        line = dashboard.utils.plotly.line_graphic(
            [1, 2],
            [3, 4],
            {
                "title": "Line",
                "x_title": "X",
                "y_title": "Y",
                "line_color": "#000000",
            },
        )
        pie = dashboard.utils.plotly.pie_graphic(
            ["A", "B"],
            [2, 1],
            {"title": "Pie"},
            show_legend=False,
        )

        self.assertEqual([bar, line, pie], ["<div>plot</div>"] * 3)
        self.assertEqual(plot.call_count, 3)

    @patch("dashboard.utils.plotly.plot", return_value="<div>plot</div>")
    def test_box_plot_skips_empty_groups_and_bins_depth_values(self, _plot):
        box = dashboard.utils.plotly.box_plot_graphic(
            [{"Empty": [], "Filled": [1, 2, 3]}],
            {"title": "Box", "width": 500, "wrap_labels": 5},
        )
        binned = dashboard.utils.plotly.box_plot_graphic_bins(
            [50, 600, 6000],
            [1, 2, 3],
            {"title": "Bins", "x_title": "Depth", "y_title": "Samples"},
        )

        self.assertEqual(box, "<div>plot</div>")
        self.assertEqual(binned, "<div>plot</div>")

    @patch("dashboard.utils.plotly.plot", return_value="<div>ridge</div>")
    @patch("dashboard.utils.plotly.ridgeplot")
    def test_ridge_plot_builds_density_figure(self, ridgeplot, plot):
        figure = go.Figure()
        ridgeplot.return_value = figure

        result = dashboard.utils.plotly.ridge_plot_graphic(
            [{"Kit A": [20, 21], "Kit B": [30, 31]}],
            {"title": "Ridge"},
        )

        self.assertEqual(result, "<div>ridge</div>")
        ridgeplot.assert_called_once()
        self.assertEqual(ridgeplot.call_args.kwargs["labels"], ["Kit A", "Kit B"])
        plot.assert_called_once_with(
            figure,
            output_type="div",
            include_plotlyjs=False,
            config=dashboard.utils.plotly.PLOTLY_CONFIG,
        )


class VariantDashboardFigureTests(SimpleTestCase):
    def test_needle_initial_arguments_and_empty_figure_are_descriptive(self):
        arguments = (
            dashboard.utils.var_needle_mutation_graph_by_lineage.build_needle_plot_initial_arguments(
                ["JN.1", "XFG.3"],
                "XFG.3",
            )
        )
        empty = (
            dashboard.utils.var_needle_mutation_graph_by_lineage.empty_needle_plot_figure()
        )

        self.assertEqual(
            arguments["needleplot-select-lineage"]["value"],
            "XFG.3",
        )
        self.assertEqual(
            arguments["needleplot-select-lineage"]["options"],
            [
                {"label": "JN.1", "value": "JN.1"},
                {"label": "XFG.3", "value": "XFG.3"},
            ],
        )
        self.assertEqual(empty.layout.xaxis.title.text, "Genome Position")

    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages",
        return_value=(None, None, None),
    )
    def test_needle_figure_returns_empty_state_without_mutations(self, _data):
        figure, text = (
            dashboard.utils.var_needle_mutation_graph_by_lineage.build_needle_plot_figure(
                "XFG.3"
            )
        )

        self.assertEqual(text, "No lineage mutations available")
        self.assertEqual(figure.layout.xaxis.title.text, "Genome Position")

    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value={
            "XFG.3": {
                "SamplesWithLineage": 2,
                "x": [100],
            }
        },
    )
    def test_variant_data_selects_first_lineage_when_none_requested(self, _cache):
        data, lineage, samples = (
            dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages(
                graphic_name="variations_per_lineage"
            )
        )

        self.assertEqual(lineage, "XFG.3")
        self.assertEqual(samples, 2)
        self.assertEqual(data["x"], [100])

    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.dashboard.utils.generic_process_data.pre_proc_variations_per_lineage",
        return_value={"ERROR": "Unable to preprocess"},
    )
    @patch(
        "dashboard.utils.var_needle_mutation_graph_by_lineage.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value=None,
    )
    def test_variant_data_propagates_preprocessing_error(
        self,
        _cache,
        _preprocess,
    ):
        self.assertEqual(
            dashboard.utils.var_needle_mutation_graph_by_lineage.get_variant_data_from_lineages(
                graphic_name="variations_per_lineage"
            ),
            {"ERROR": "Unable to preprocess"},
        )


class BioinfoMethodologyTests(SimpleTestCase):
    def cached_data(self, graphic_name):
        return {
            "bioinfo_percentage_data": {
                "Mapped reads": [90, 95],
                "Invalid series": "not-a-list",
            },
            "depth_variant_consensus": {
                "10": [1, 3],
                "20": [2, 4],
                "invalid": [5],
                "30": "not-a-list",
            },
            "depth_samples_in_run": {
                "5": [2, 4],
                "15": [6, 8],
            },
        }[graphic_name]

    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.plotly.box_plot_graphic_bins",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.plotly.ridge_plot_graphic",
        return_value="<div>ridge</div>",
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_bioinfo_graphics_builds_cached_percentage_and_depth_plots(
        self,
        cached,
        ridge,
        box,
    ):
        cached.side_effect = self.cached_data

        result = dashboard.utils.met_bioinfo.bioinfo_graphics()

        self.assertEqual(
            result,
            {
                "boxplot_comparation": "<div>ridge</div>",
                "depth_variants": "<div>box</div>",
                "depth_sample_run": "<div>box</div>",
            },
        )
        ridge.assert_called_once_with(
            [{"Mapped reads": [90, 95]}],
            {"title": "Density Plot Percentage"},
        )
        self.assertEqual(box.call_count, 2)
        self.assertEqual(box.call_args_list[0].args[:2], ([10.0, 20.0], [2, 3]))

    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.generic_process_data.pre_proc_bioinfo_percentage_data",
        return_value={"ERROR": "No percentages"},
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.generic_process_data.pre_proc_depth_sample_run",
        return_value={"ERROR": "No sample depth"},
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.generic_process_data.pre_proc_depth_variants",
        return_value={"ERROR": "No variants"},
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value=None,
    )
    def test_bioinfo_graphics_returns_error_when_no_source_can_be_processed(
        self,
        _cached,
        _variants,
        _sample_depth,
        _percentage,
    ):
        self.assertEqual(
            dashboard.utils.met_bioinfo.bioinfo_graphics(),
            {"ERROR": dashboard.dashboard_config.ERROR_NOT_DATA_LOADED_YET},
        )

    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.plotly.box_plot_graphic_bins",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.plotly.ridge_plot_graphic"
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_bioinfo_graphics_skips_empty_percentage_series(
        self,
        cached,
        ridge,
        _box,
    ):
        cached.side_effect = lambda name: (
            {"Empty": []}
            if name == "bioinfo_percentage_data"
            else {"10": [1, 2]}
        )

        result = dashboard.utils.met_bioinfo.bioinfo_graphics()

        self.assertNotIn("boxplot_comparation", result)
        ridge.assert_not_called()

    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.generic_process_data.pre_proc_bioinfo_percentage_data",
        return_value={"SUCCESS": "success"},
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.generic_process_data.pre_proc_depth_sample_run",
        return_value={"SUCCESS": "success"},
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.generic_process_data.pre_proc_depth_variants",
        return_value={"SUCCESS": "success"},
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.plotly.box_plot_graphic_bins",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.plotly.ridge_plot_graphic",
        return_value="<div>ridge</div>",
    )
    @patch(
        "dashboard.utils.met_bioinfo.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_bioinfo_graphics_preprocesses_missing_caches_successfully(
        self,
        cached,
        ridge,
        box,
        preprocess_variants,
        preprocess_sample_run,
        preprocess_percentage,
    ):
        cached.side_effect = [
            None,
            {"Mapped reads": [90, 95]},
            None,
            {"10": [1, 3]},
            None,
            {"5": [2, 4]},
        ]

        result = dashboard.utils.met_bioinfo.bioinfo_graphics()

        self.assertEqual(
            result,
            {
                "boxplot_comparation": "<div>ridge</div>",
                "depth_variants": "<div>box</div>",
                "depth_sample_run": "<div>box</div>",
            },
        )
        preprocess_percentage.assert_called_once_with()
        preprocess_variants.assert_called_once_with()
        preprocess_sample_run.assert_called_once_with()
        ridge.assert_called_once()
        self.assertEqual(box.call_count, 2)


class HostMethodologyTests(SimpleTestCase):
    def host_payload(self, invalid=None):
        return {
            "gender_label": ["Male", "Female"],
            "gender_values": [3, 2],
            "gender_data": [
                ["0-18", 1, 1, 0],
                ["19-40", 2, 1, 0],
            ],
            "host_age_data": {"0-18": 2, "19-40": 3},
            "invalid_data": invalid or {"age": 0, "gender": 0},
        }

    @patch(
        "dashboard.utils.met_host_info.dashboard.utils.plotly.bar_graphic",
        side_effect=["<div>gender-age</div>", "<div>age</div>"],
    )
    @patch(
        "dashboard.utils.met_host_info.dashboard.utils.plotly.pie_graphic",
        return_value="<div>gender</div>",
    )
    @patch(
        "dashboard.utils.met_host_info.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_host_graphics_builds_all_cached_figures(
        self,
        cached,
        _pie,
        bar,
    ):
        cached.return_value = self.host_payload()

        result = dashboard.utils.met_host_info.host_info_graphics()

        self.assertEqual(
            result,
            {
                "gender_graph": "<div>gender</div>",
                "gender_age_graph": "<div>gender-age</div>",
                "range_age_graph": "<div>age</div>",
            },
        )
        self.assertEqual(bar.call_count, 2)

    @patch(
        "dashboard.utils.met_host_info.dashboard.utils.plotly.bar_graphic",
        return_value="<div>bar</div>",
    )
    @patch(
        "dashboard.utils.met_host_info.dashboard.utils.plotly.pie_graphic",
        return_value="<div>pie</div>",
    )
    @patch(
        "dashboard.utils.met_host_info.dashboard.utils.generic_process_data.pre_proc_host_info"
    )
    @patch(
        "dashboard.utils.met_host_info.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_host_graphics_preprocesses_missing_cache_and_counts_invalid_data(
        self,
        cached,
        preprocess,
        _pie,
        _bar,
    ):
        cached.side_effect = [None, self.host_payload({"age": 2, "gender": 1})]

        result = dashboard.utils.met_host_info.host_info_graphics()

        preprocess.assert_called_once_with()
        self.assertEqual(result["invalid_data"], 3)


class SampleProcessingMethodologyTests(SimpleTestCase):
    def cached_data(self, graphic_name):
        return {
            "nucleic_acid_extraction_protocol": {
                "": 2,
                "Kit A": 3,
                None: 1,
            },
            "extraction_protocol_pcr_1": {
                "Kit A": {"20": 2, "bad": 1, "41": 3},
            },
            "specimen_source_pcr_1": {
                "Nasopharyngeal": {"18": 2, "25": 1},
            },
            "calculation_date": {
                "Defined-Bioinfo": [1, 2, 3],
            },
        }[graphic_name]

    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.box_plot_graphic",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.bar_graphic",
        return_value="<div>bar</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_sample_processing_graphics_builds_all_cached_figures(
        self,
        cached,
        bar,
        box,
    ):
        cached.side_effect = self.cached_data

        result = dashboard.utils.met_sample_preprocessing.sample_processing_graphics()

        self.assertEqual(
            result,
            {
                "nucleic_protocol": "<div>bar</div>",
                "cts_extraction": "<div>box</div>",
                "cts_specimen": "<div>box</div>",
                "calculation_date": "<div>box</div>",
            },
        )
        protocol_df = bar.call_args.kwargs["data"]
        self.assertEqual(
            dict(zip(protocol_df["protocol"], protocol_df["number"])),
            {"Kit A": 3, "Not Provided": 3},
        )
        self.assertEqual(box.call_count, 3)

    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_process_data.pre_proc_nucleic_acid_extraction_protocol",
        return_value={"ERROR": "No extraction data"},
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value=None,
    )
    def test_sample_processing_returns_extraction_preprocessing_error(
        self,
        _cached,
        _preprocess,
    ):
        self.assertEqual(
            dashboard.utils.met_sample_preprocessing.sample_processing_graphics(),
            {"ERROR": "No extraction data"},
        )

    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.box_plot_graphic",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.bar_graphic",
        return_value="<div>bar</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_process_data.pre_proc_nucleic_acid_extraction_protocol",
        return_value={"SUCCESS": "Success"},
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_sample_processing_preprocesses_missing_nucleic_protocol_cache(
        self,
        cached,
        preprocess,
        bar,
        _box,
    ):
        cached.side_effect = [
            None,
            {"": 1, "Kit A": 2},
            self.cached_data("extraction_protocol_pcr_1"),
            self.cached_data("specimen_source_pcr_1"),
            self.cached_data("calculation_date"),
        ]

        result = dashboard.utils.met_sample_preprocessing.sample_processing_graphics()

        self.assertEqual(result["nucleic_protocol"], "<div>bar</div>")
        preprocess.assert_called_once_with()
        protocol_df = bar.call_args.kwargs["data"]
        self.assertEqual(
            dict(zip(protocol_df["protocol"], protocol_df["number"])),
            {"Kit A": 2, "Not Provided": 1},
        )

    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.box_plot_graphic",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.bar_graphic",
        return_value="<div>bar</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_process_data.pre_proc_extraction_protocol_pcr_1",
        return_value={"ERROR": "No extraction Ct data"},
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_sample_processing_passes_extraction_ct_preprocessing_error_to_box_plot(
        self,
        cached,
        _preprocess,
        _bar,
        box,
    ):
        cached.side_effect = [
            self.cached_data("nucleic_acid_extraction_protocol"),
            None,
            self.cached_data("specimen_source_pcr_1"),
            self.cached_data("calculation_date"),
        ]

        result = dashboard.utils.met_sample_preprocessing.sample_processing_graphics()

        self.assertEqual(result["cts_extraction"], "<div>box</div>")
        self.assertEqual(
            box.call_args_list[0].args[0],
            {"ERROR": "No extraction Ct data"},
        )

    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.box_plot_graphic",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.bar_graphic",
        return_value="<div>bar</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_process_data.pre_proc_extraction_protocol_pcr_1",
        return_value={"SUCCESS": "Success"},
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_sample_processing_preprocesses_missing_ct_extraction_data(
        self,
        cached,
        preprocess,
        _bar,
        box,
    ):
        cached.side_effect = [
            self.cached_data("nucleic_acid_extraction_protocol"),
            None,
            {"Kit A": {"20": 2}},
            self.cached_data("specimen_source_pcr_1"),
            self.cached_data("calculation_date"),
        ]

        result = dashboard.utils.met_sample_preprocessing.sample_processing_graphics()

        self.assertEqual(result["cts_extraction"], "<div>box</div>")
        preprocess.assert_called_once_with()
        self.assertEqual(box.call_count, 3)

    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.box_plot_graphic",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.bar_graphic",
        return_value="<div>bar</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_process_data.pre_proc_specimen_source_pcr_1",
        return_value={"ERROR": "No specimen data"},
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_sample_processing_returns_specimen_preprocessing_error(
        self,
        cached,
        _preprocess,
        _bar,
        box,
    ):
        cached.side_effect = [
            self.cached_data("nucleic_acid_extraction_protocol"),
            self.cached_data("extraction_protocol_pcr_1"),
            None,
            self.cached_data("calculation_date"),
        ]

        result = dashboard.utils.met_sample_preprocessing.sample_processing_graphics()

        self.assertEqual(result["cts_specimen"], "<div>box</div>")
        self.assertEqual(box.call_args_list[1].args[0], {"ERROR": "No specimen data"})

    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.box_plot_graphic",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.plotly.bar_graphic",
        return_value="<div>bar</div>",
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_process_data.pre_proc_calculation_date",
        return_value={"ERROR": "No date data"},
    )
    @patch(
        "dashboard.utils.met_sample_preprocessing.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_sample_processing_returns_calculation_date_preprocessing_error(
        self,
        cached,
        _preprocess,
        _bar,
        box,
    ):
        cached.side_effect = [
            self.cached_data("nucleic_acid_extraction_protocol"),
            self.cached_data("extraction_protocol_pcr_1"),
            self.cached_data("specimen_source_pcr_1"),
            None,
        ]

        result = dashboard.utils.met_sample_preprocessing.sample_processing_graphics()

        self.assertEqual(result["calculation_date"], "<div>box</div>")
        self.assertEqual(box.call_args_list[-1].args[0], {"ERROR": "No date data"})


class SequencingMethodologyTests(SimpleTestCase):
    def cached_data(self, graphic_name):
        return {
            "sequencing_instrument_platform": {"ILLUMINA": 4},
            "sequencing_instrument_model": {"NextSeq": 4},
            "library_preparation_kit": {"": 1, "Nextera": 3},
            "read_length": {"150": 3, "invalid": 2, "151": 1},
            "library_kit_pcr_1": {
                "Nextera": {"20": 2, "20,5": 1, "bad": 1, "41": 2},
            },
            "ct_number_of_base_pairs_sequenced": {
                "1000": [20, 30, 50, "bad"],
                "invalid": [25],
                "2000": [45],
            },
        }[graphic_name]

    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.plotly.line_graphic",
        return_value="<div>line</div>",
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.plotly.box_plot_graphic",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.plotly.bar_graphic",
        return_value="<div>bar</div>",
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_sequencing_graphics_builds_all_cached_figures(
        self,
        cached,
        bar,
        box,
        line,
    ):
        cached.side_effect = self.cached_data

        result = dashboard.utils.met_sequencing.sequencing_graphics()

        self.assertEqual(
            result,
            {
                "instrument_platform": "<div>bar</div>",
                "instrument_model": "<div>bar</div>",
                "library_preparation": "<div>bar</div>",
                "read_length": "<div>bar</div>",
                "cts_library": "<div>box</div>",
                "number_of_base": "<div>line</div>",
            },
        )
        self.assertEqual(bar.call_count, 4)
        self.assertEqual(box.call_count, 1)
        self.assertEqual(line.call_args.args[:2], ([1000], [25]))

    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.generic_process_data.pre_proc_sequencing_instrument_model",
        return_value={"SUCCESS": "success"},
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.plotly.line_graphic",
        return_value="<div>line</div>",
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.plotly.box_plot_graphic",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.plotly.bar_graphic",
        return_value="<div>bar</div>",
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_sequencing_graphics_preprocesses_missing_model_cache(
        self,
        cached,
        _bar,
        _box,
        _line,
        preprocess_model,
    ):
        def cache_lookup(graphic_name):
            if graphic_name == "sequencing_instrument_model":
                return cache_lookup.model_values.pop(0)
            return self.cached_data(graphic_name)

        cache_lookup.model_values = [None, {"MiSeq": 2}]
        cached.side_effect = cache_lookup

        result = dashboard.utils.met_sequencing.sequencing_graphics()

        self.assertEqual(result["instrument_model"], "<div>bar</div>")
        preprocess_model.assert_called_once_with()

    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.generic_process_data.pre_proc_library_kit_pcr_1",
        return_value={"ERROR": "No CT data"},
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.plotly.line_graphic",
        return_value="<div>line</div>",
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.plotly.box_plot_graphic",
        return_value="<div>box</div>",
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.plotly.bar_graphic",
        return_value="<div>bar</div>",
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.generic_graphic_data.get_graphic_json_data"
    )
    def test_sequencing_graphics_passes_ct_preprocessing_error_to_box_plot(
        self,
        cached,
        _bar,
        box,
        _line,
        preprocess_library,
    ):
        def cache_lookup(graphic_name):
            if graphic_name == "library_kit_pcr_1":
                return None
            return self.cached_data(graphic_name)

        cached.side_effect = cache_lookup

        result = dashboard.utils.met_sequencing.sequencing_graphics()

        self.assertEqual(result["cts_library"], "<div>box</div>")
        preprocess_library.assert_called_once_with()
        self.assertEqual(box.call_args.args[0], {"ERROR": "No CT data"})

    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.generic_process_data.pre_proc_sequencing_instrument_platform",
        return_value={"ERROR": "No sequencing data"},
    )
    @patch(
        "dashboard.utils.met_sequencing.dashboard.utils.generic_graphic_data.get_graphic_json_data",
        return_value=None,
    )
    def test_sequencing_returns_platform_preprocessing_error(
        self,
        _cached,
        _preprocess,
    ):
        self.assertEqual(
            dashboard.utils.met_sequencing.sequencing_graphics(),
            {"ERROR": "No sequencing data"},
        )
