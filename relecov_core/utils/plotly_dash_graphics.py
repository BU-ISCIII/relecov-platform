from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
from dash import dcc, html
import plotly.express as px
from dash.exceptions import PreventUpdate


# from relecov_core.utils.handling_samples import get_sample_per_date_per_lab


def dash_bar_lab(option_list, data):

    option = []
    for opt_list in option_list:
        option.append({"label": opt_list, "value": opt_list})

    app = DjangoDash("samplePerLabGraphic")
    empty_fig = px.bar(x=[0], y=[0], height=300)

    app.layout = html.Div(
        [
            html.H4("Select the lab"),
            html.Div(
                [
                    dcc.Dropdown(
                        id="select_lab_name",
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
        Input("select_lab_name", "value"),
    )
    def update_graph(select_lab_name):
        if select_lab_name == 1:
            raise PreventUpdate
        sub_data = data[data.lab_name == select_lab_name]
        graph = px.bar(
            sub_data,
            x=sub_data["date"],
            y=sub_data["num_samples"],
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
            title="Register samples",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45,
            margin=dict(l=20, r=40, t=30, b=20),
            xaxis_title="Sequencing dates",
            yaxis_title="Number of samples",
        )
        return graph, f"Laboratory selected: {select_lab_name}"
