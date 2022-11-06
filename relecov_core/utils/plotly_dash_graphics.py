from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output
from dash import dcc, html
import plotly.express as px
from plotly.offline import plot


# from relecov_core.utils.handling_samples import get_sample_per_date_per_lab


def dash_bar_lab(option_list, data):
    def select_option(option, data):
        """Return the sub data frame for the selected option"""
        sub_df = data[data.lab_name == option]
        # import pdb; pdb.set_trace()
        return sub_df

    option = []
    for opt_list in option_list:
        option.append({"label": opt_list, "value": opt_list})

    app = DjangoDash("samplePerLabGraphic")

    """
    if len(option) == 1:
        graph = px.bar(
            data, text_auto=True
            # data, y=col_names[1], x=col_names[0], text_auto=True, width=options["width"]
        )
        # Customize aspect
        graph.update_traces(
            marker_color="rgb(158,202,225)",
            marker_line_color="rgb(8,48,107)",
            marker_line_width=1.5,
            opacity=0.6,
        )
        graph.update_layout(
            title=options["title"],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-45,
            margin=dict(l=20, r=40, t=30, b=20),
        )

        plot_div = plot(graph, output_type="div", config={"displaylogo": False})

    else:
        import pdb; pdb.set_trace()
    """

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
            html.Div(id="my_selection"),
            dcc.Graph(id="bar_graph", figure={}),
        ]
    )

    @app.callback(
        Output("bar_graph", "figure"),
        Output("my_selection", "children"),
        Input("select_lab_name", "value"),
    )
    def update_graph(select_lab_name):
        if select_lab_name == 1:
            return None
        sub_data = data[data.lab_name == select_lab_name]
        graph = px.bar(
            sub_data, x=sub_data["date"], y=sub_data["num_samples"], text_auto=True
        )
        return graph, f"Laboratory selected: {select_lab_name}"
