from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

import core.utils.plotly_dash_graphics

APP_NAME = "samplePerLabGraphic"


def _empty_figure():
    fig = go.Figure()
    fig.update_layout(
        title="No data available for the selected laboratory",
        template=core.utils.plotly_dash_graphics.mi_template,
        xaxis_title="Collecting date (ISOWeeks)",
        yaxis_title="Number of samples",
        margin=dict(l=20, r=40, t=30, b=20),
    )
    return fig


def register():
    app = DjangoDash(
        APP_NAME,
        external_stylesheets=[
            "/static/core/custom/css/dash_style.css",
        ],
    )

    app.layout = html.Div(
        [
            html.H4("Select the laboratory", style={"fontFamily": "Oxanium, sans-serif"}),
            dcc.Dropdown(
                id="select_collecting_inst",
                options=[],
                clearable=False,
                multi=False,
                value=None,
                style={"width": "400px"},
            ),
            dcc.Store(id="sample_per_lab_data", data=[]),
            html.Br(),
            dcc.Graph(id="bar_graph", figure=_empty_figure()),
        ]
    )

    @app.callback(
        Output("bar_graph", "figure"),
        Input("select_collecting_inst", "value"),
        State("sample_per_lab_data", "data"),
    )
    def update_graph(select_collecting_inst, data):
        if not select_collecting_inst:
            raise PreventUpdate
        df = pd.DataFrame(data or [])
        if df.empty:
            return _empty_figure()

        selected = str(select_collecting_inst)
        if "lab_code_1" in df.columns:
            mask = df["lab_code_1"].fillna("").astype(str) == selected
            fallback_mask = pd.Series(False, index=df.index)
            for column in [
                col
                for col in ["collecting_institution", "legacy_collecting_institution"]
                if col in df.columns
            ]:
                fallback_mask = fallback_mask | (
                    df[column].fillna("").astype(str) == selected
                )
            df = df[mask | fallback_mask]
        elif "collecting_institution" in df.columns:
            df = df[df["collecting_institution"].fillna("").astype(str) == selected]
        else:
            df = df.iloc[0:0]

        if df.empty:
            return _empty_figure()

        sub_data = df.drop_duplicates(subset=["iso_yearweek"]).reset_index(drop=True)
        sub_data["iso_yearweek"] = (
            sub_data["iso_yearweek"]
            .astype(str)
            .str.replace(r"W(\d{1})$", r"W0\1", regex=True)
        )
        sub_data["num_samples"] = (
            pd.to_numeric(sub_data["num_samples"], errors="coerce")
            .fillna(0)
            .astype(int)
        )
        sub_data = sub_data.sort_values("iso_yearweek")

        graph = px.bar(
            sub_data,
            x=sub_data["iso_yearweek"].astype(str),
            y=sub_data["num_samples"].astype(int),
            text_auto=True,
        )
        graph.update_traces(
            marker=dict(color=core.utils.plotly_dash_graphics.COLOR_PALETTE[1]),
            opacity=0.6,
        )
        graph.update_layout(
            title="Registered samples over time",
            autotypenumbers="convert types",
            template=core.utils.plotly_dash_graphics.mi_template,
            xaxis_tickangle=-45,
            margin=dict(l=20, r=40, t=30, b=20),
            xaxis_title="Collecting date (ISOWeeks)",
            yaxis_title="Number of samples",
        )
        return graph
