import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash
from django.shortcuts import redirect


def render_page_content():
    # app = dash.Dash(m_utilization, external_stylesheets=[dbc.themes.BOOTSTRAP])
    app = DjangoDash("m_utilization", external_stylesheets=[dbc.themes.BOOTSTRAP])
    # the style arguments for the sidebar. We use position:fixed and a fixed width
    SIDEBAR_STYLE = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "16rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }
    CONTENT_STYLE = {
        "transition": "margin-left .5s",
        "margin-left": "18rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }

    sidebar = html.Div(
        [
            html.H4("Methodology Dashboard"),
            html.Hr(),
            html.P("A simple sidebar layout with navigation links", className="lead"),
            dbc.Nav(
                [
                    dbc.NavLink("Home", href="/dashboard/variants", active="exact"),
                    dbc.NavLink("Page 1", href="/page-1", active="exact"),
                    dbc.NavLink("Page 2", href="/page-2", active="exact"),
                ],
                vertical=True,
                pills=True,
            ),
        ],
        style=SIDEBAR_STYLE,
    )
    content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

    app.layout = html.Div([dcc.Location(id="url"), sidebar, content])

    @app.callback(Output("page-content", "children"), [Input("url", "pathname")])
    def render_page_content(pathname):
        if pathname in ["/", "/dashboard/variants"]:
            return redirect("/dashboard_variants")
            return html.P("This is the content of page 1!")
        elif pathname == "/page-2":
            return html.P("This is the content of page 2. Yay!")
        elif pathname == "/page-3":
            return html.P("Oh cool, this is page 3!")
        # If the user tries to reach a different page, return a 404 message
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )


import dash_daq as daq


def create_gauge(value, label):
    app = DjangoDash("param_empty", external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = html.Div(
        style={"font-size": "2rem", "color": "green"},
        children=[
            daq.Gauge(
                showCurrentValue=True,
                color={
                    "gradient": True,
                    "ranges": {"red": [0, 40], "yellow": [40, 80], "green": [80, 100]},
                },
                id="my-gauge-1",
                label={"label": label, "style": {"font-size": "2rem"}},
                value=value,
                units="%",
                max=100,
                min=0,
            ),
        ],
    )

    @app.callback(Output("my-gauge-1", "value"), Input("my-gauge-slider-1", "value"))
    def update_output(value):
        return value
