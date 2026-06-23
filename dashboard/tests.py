from unittest.mock import patch

import pandas as pd
from django.test import SimpleTestCase

import dashboard.utils.generic_process_data
import dashboard.utils.met_index
import dashboard.utils.var_lineage_variation_over_time_graph
import dashboard.utils.var_samples_received_over_time_pie


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

    def test_received_sample_dataframes_are_sorted_by_count(self):
        data = {
            "region": {"Madrid": 7, "Canarias": 2},
            "laboratory": {"Lab B": 9, "Lab A": 1},
        }

        regions = dashboard.utils.var_samples_received_over_time_pie.create_samples_per_ccaa_dataframe(
            data
        )
        laboratories = dashboard.utils.var_samples_received_over_time_pie.create_samples_per_laboratory_dataframe(
            data
        )

        self.assertEqual(regions["CCAA_NAME"].tolist(), ["Canarias", "Madrid"])
        self.assertEqual(laboratories["LABORATORY_NAME"].tolist(), ["Lab A", "Lab B"])


class MethodologyDashboardTests(SimpleTestCase):
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
