from dash import dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

import dashboard.utils.var_heatmap_mutation_graph_by_lineage

APP_NAME = "mutationHeatmap"


def register():
    app = DjangoDash(APP_NAME)

    def serve_layout():
        sample_ids, genes = (
            dashboard.utils.var_heatmap_mutation_graph_by_lineage.get_heatmap_options()
        )
        figure = dashboard.utils.var_heatmap_mutation_graph_by_lineage.create_heatmap(
            sample_ids, genes
        )
        return html.Div(
            children=[
                html.Div(
                    style={
                        "display": "flex",
                        "justify-content": "space-between",
                        "align-items": "flex-start",
                    },
                    children=[
                        html.P("Select samples"),
                        html.P("Select genes"),
                    ],
                ),
                html.Div(
                    style={
                        "display": "flex",
                        "justify-content": "start",
                        "align-items": "flex-start",
                    },
                    children=[
                        dcc.Dropdown(
                            id="mutation_heatmap_select_sample",
                            options=[{"label": i, "value": i} for i in sample_ids],
                            clearable=False,
                            multi=True,
                            value=sample_ids,
                            style={"width": "390px", "margin-right": "30px"},
                        ),
                        dcc.Dropdown(
                            id="mutation_heatmap_gene_dropdown",
                            options=[{"label": i, "value": i} for i in genes],
                            clearable=False,
                            multi=True,
                            value=genes,
                            style={"width": "390px", "margin-right": "35px"},
                        ),
                    ],
                ),
                dcc.Graph(
                    id="mutation_heatmap_graph",
                    figure=figure,
                ),
            ]
        )

    app.layout = serve_layout

    @app.callback(
        Output("mutation_heatmap_graph", "figure"),
        Input("mutation_heatmap_select_sample", "value"),
        Input("mutation_heatmap_gene_dropdown", "value"),
    )
    def update_selected_sample(selected_sample, selected_genes):
        selected_sample = list(selected_sample or [])
        selected_genes = list(selected_genes or [])
        return dashboard.utils.var_heatmap_mutation_graph_by_lineage.create_heatmap(
            selected_sample, selected_genes
        )
