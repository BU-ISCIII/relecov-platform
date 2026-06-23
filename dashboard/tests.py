from unittest.mock import patch

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
import dashboard.utils.var_heatmap_mutation_graph_by_lineage
import dashboard.utils.var_lineage_variation_over_time_graph
import dashboard.utils.var_needle_mutation_graph_by_lineage
import dashboard.utils.var_samples_received_over_time_pie
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
        "dashboard.views.dashboard.utils.var_molecule3D_bn_graph.create_model3D_bn"
    )
    def test_spike_mutations_builds_model_before_rendering(self, create_model, render):
        dashboard.views.spike_mutations_3d(self.request)

        create_model.assert_called_once_with()
        render.assert_called_once_with(
            self.request,
            "dashboard/variantSpikeMutations3D.html",
        )

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

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.core.utils.variants.get_all_chromosome_objs",
        return_value=None,
    )
    def test_heatmap_view_reports_missing_chromosome(self, _chromosomes, render):
        dashboard.views.variants_mutations_in_lineages_heatmap(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ERROR": core.config.ERROR_CHROMOSOME_NOT_DEFINED_IN_DATABASE},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.core.utils.variants.get_gene_list",
        return_value=[],
    )
    @patch(
        "dashboard.views.core.utils.variants.get_all_chromosome_objs",
        return_value=[object()],
    )
    def test_heatmap_view_reports_missing_genes(
        self,
        _chromosomes,
        _genes,
        render,
    ):
        dashboard.views.variants_mutations_in_lineages_heatmap(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ERROR": core.config.ERROR_GENE_NOT_DEFINED_IN_DATABASE},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.core.utils.variants.get_sample_in_variant_list",
        return_value=[],
    )
    @patch(
        "dashboard.views.core.utils.variants.get_gene_list",
        return_value=["S"],
    )
    @patch(
        "dashboard.views.core.utils.variants.get_all_chromosome_objs",
        return_value=[object()],
    )
    def test_heatmap_view_reports_missing_variant_samples(
        self,
        _chromosomes,
        _genes,
        _samples,
        render,
    ):
        dashboard.views.variants_mutations_in_lineages_heatmap(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/variantsMutationsInLineagesHeatmap.html",
            {"ERROR": core.config.ERROR_VARIANT_IN_SAMPLE_NOT_DEFINED},
        )

    @patch("dashboard.views.render")
    @patch(
        "dashboard.views.core.utils.variants.get_sample_in_variant_list",
        return_value=["SAMPLE-1"],
    )
    @patch(
        "dashboard.views.core.utils.variants.get_gene_list",
        return_value=["S"],
    )
    @patch(
        "dashboard.views.core.utils.variants.get_all_chromosome_objs",
        return_value=[object()],
    )
    def test_heatmap_view_renders_when_required_data_exists(
        self,
        _chromosomes,
        _genes,
        _samples,
        render,
    ):
        dashboard.views.variants_mutations_in_lineages_heatmap(self.request)

        render.assert_called_once_with(
            self.request,
            "dashboard/variantsMutationsInLineagesHeatmap.html",
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


class VariantDashboardFigureTests(SimpleTestCase):
    def test_heatmap_default_options_handle_missing_chromosome(self):
        with patch(
            "dashboard.utils.var_heatmap_mutation_graph_by_lineage.core.utils.variants.get_default_chromosome",
            return_value=None,
        ):
            samples, genes = (
                dashboard.utils.var_heatmap_mutation_graph_by_lineage.get_default_sample_and_gene_options()
            )

        self.assertEqual(samples, [])
        self.assertEqual(genes, [])

    def test_heatmap_returns_empty_and_populated_figures(self):
        empty = (
            dashboard.utils.var_heatmap_mutation_graph_by_lineage.get_figure(
                pd.DataFrame(),
                [],
                [],
            )
        )
        populated = (
            dashboard.utils.var_heatmap_mutation_graph_by_lineage.get_figure(
                pd.DataFrame(
                    {
                        "SAMPLE": ["S1", "S2"],
                        "POS": [100, 200],
                        "MUTATION": ["N501Y", "D614G"],
                        "AF": [0.8, 0.4],
                        "EFFECT": ["missense", "missense"],
                        "GENE": ["S", "S"],
                        "LINEAGE": ["XFG.3", "JN.1"],
                    }
                ),
                ["S1", "S2"],
                ["S"],
            )
        )

        self.assertEqual(empty.layout.title.text, "No mutation data available")
        self.assertEqual(populated.layout.yaxis.title.text, "Samples")
        self.assertEqual(populated.layout.xaxis.title.text, "Mutations")
        self.assertEqual(populated.data[0].z.shape, (2, 2))

    @patch(
        "dashboard.utils.var_heatmap_mutation_graph_by_lineage.create_dataframe",
        return_value=pd.DataFrame(
            {"SAMPLE": ["S1"], "GENE": ["S"], "POS": [1], "MUTATION": ["M"]}
        ),
    )
    @patch(
        "dashboard.utils.var_heatmap_mutation_graph_by_lineage.get_default_sample_and_gene_options",
        return_value=(["fallback-sample"], ["fallback-gene"]),
    )
    def test_heatmap_options_prefer_values_from_dataframe(
        self,
        _defaults,
        _dataframe,
    ):
        samples, genes = (
            dashboard.utils.var_heatmap_mutation_graph_by_lineage.get_heatmap_options()
        )

        self.assertEqual(samples, ["S1"])
        self.assertEqual(genes, ["S"])

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
