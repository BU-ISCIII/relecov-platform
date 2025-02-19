# Generic imports
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
from dash import dcc, html
import plotly.express as px
from dash.exceptions import PreventUpdate


def dash_bar_lab(option_list, data):
    option = []
    for opt_list in option_list:
        option.append({"label": opt_list, "value": opt_list})
    app = DjangoDash("samplePerLabGraphic")
    empty_fig = px.bar(x=[0], y=[0], height=300)

    app.layout = html.Div(
        [
            html.H4("Select the collecting institution"),
            html.Div(
                [
                    dcc.Dropdown(
                        id="select_collecting_inst",
                        options=option,
                        clearable=False,
                        multi=False,
                        value=1,
                        style={"width": "400px"},
                    ),
                ]
            ),
            html.Br(),
            html.Div(id="lab_selection"),
            dcc.Graph(id="bar_graph", figure=empty_fig),
        ]
    )

    @app.callback(
        Output("bar_graph", "figure"),
        Output("lab_selection", "children"),
        Input("select_collecting_inst", "value"),
    )
    def update_graph(select_collecting_inst):
        if select_collecting_inst is None or select_collecting_inst == 1:
            raise PreventUpdate
        sub_data = data[data.collecting_institution == select_collecting_inst]
        sub_data = sub_data.drop_duplicates(subset=["iso_yearweek"]).reset_index(drop=True)
        sub_data["iso_yearweek"] = sub_data["iso_yearweek"].str.replace(
            r"W(\d{1})$", r"W0\1", regex=True
        ) # Add padding: W5 -> W05
        sub_data["num_samples"] = sub_data["num_samples"].astype(int)
        sub_data = sub_data.sort_values("iso_yearweek")
        if sub_data.empty:
            # Return an empty figure if no data is available
            return (
                empty_fig,
                f"Laboratory selected: {select_collecting_inst} (No data available)",
            )
        graph = px.bar(
            sub_data,
            x=sub_data["iso_yearweek"].astype(str),
            y=sub_data["num_samples"].astype(int),
            text_auto=True,
            width=520,
            height=300,
        )
        graph.update_traces(
            marker_color="rgb(0,179,0)",
            marker_line_color="rgb(8,48,107)",
            marker_line_width=1.5,
            opacity=0.6,
        )
        graph.update_layout(
            title="Registered samples over time",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45,
            margin=dict(l=20, r=40, t=30, b=20),
            xaxis_title="Collecting date (ISOWeeks)",
            yaxis_title="Number of samples",
        )
        return graph, f"Laboratory selected: {select_collecting_inst}"
