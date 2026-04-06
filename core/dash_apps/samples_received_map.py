from dash import dcc, html
from dash.dependencies import Input, Output
from django_plotly_dash import DjangoDash

import core.utils.samples_map


APP_NAME = "samplesReceivedOverTimeMap"


def register():
    app = DjangoDash(APP_NAME)

    app.layout = html.Div(
        children=[
            dcc.Interval(id="samples-received-map-load", interval=1, n_intervals=0, max_intervals=1),
            html.Iframe(
                id="samples-received-map-frame",
                srcDoc="",
                style={"width": "100%", "height": "800px", "border": "0"},
            ),
        ],
    )

    @app.callback(
        Output("samples-received-map-frame", "srcDoc"),
        Input("samples-received-map-load", "n_intervals"),
    )
    def load_map(_n_intervals):
        result = core.utils.samples_map.build_samples_received_map_html()
        if isinstance(result, dict) and "ERROR" in result:
            return "<h3>Unable to load received samples map</h3>"
        return result
