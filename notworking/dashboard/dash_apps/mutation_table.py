from dash import dash_table, dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

import dashboard.utils.var_lineages_mutation_table_generation

APP_NAME = "mutationTable"
PAGE_SIZE = 20


def register():
    app = DjangoDash(APP_NAME)

    def serve_layout():
        sample_ids, effects = (
            dashboard.utils.var_lineages_mutation_table_generation.get_default_sample_and_effect_options()
        )
        data = dashboard.utils.var_lineages_mutation_table_generation.create_mutation_table(
            sample_ids, effects
        )
        columns = [{"name": key, "id": key} for key in data[0].keys()] if data else []
        return html.Div(
            children=[
                html.P("Select effects"),
                dcc.Dropdown(
                    id="mutation_table-effect_dropdown",
                    options=[{"label": i, "value": i} for i in effects],
                    clearable=False,
                    multi=True,
                    value=effects,
                    style={"width": "400px"},
                    placeholder="Mutation effect",
                ),
                html.Br(),
                dash_table.DataTable(
                    id="mutation_datatable",
                    data=data,
                    columns=columns,
                    page_current=0,
                    page_size=PAGE_SIZE,
                    page_action="custom",
                ),
            ]
        )

    app.layout = serve_layout

    @app.callback(
        Output("mutation_datatable", "data"),
        Output("mutation_datatable", "columns"),
        Input("mutation_table-effect_dropdown", "value"),
    )
    def update_selected_effects(selected_effects):
        sample_ids, _ = (
            dashboard.utils.var_lineages_mutation_table_generation.get_default_sample_and_effect_options()
        )
        selected_effects = list(selected_effects or [])
        data = dashboard.utils.var_lineages_mutation_table_generation.create_mutation_table(
            sample_ids, selected_effects
        )
        columns = [{"name": key, "id": key} for key in data[0].keys()] if data else []
        return data, columns
