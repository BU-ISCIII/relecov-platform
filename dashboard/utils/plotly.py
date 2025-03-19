# Generic imports
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.graph_objects as go
from dash import html, dcc
from django_plotly_dash import DjangoDash
from plotly.offline import plot
from ridgeplot import ridgeplot
from plotly.offline import plot
import numpy as np

def graph_gauge_percent_values(app_name, value, label, size=180):
    """Create Dashboard application for showing a gauge graphic for the
    percentage  values
    """
    app = DjangoDash(app_name, external_stylesheets=[dbc.themes.BOOTSTRAP])
    graph = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"suffix": "%"},
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": label, "font": {"size": 18}},
            gauge={"axis": {"range": [None, 100]}},
        )
    )
    graph.update_layout(margin=dict(t=10, b=0, l=30, r=30), height=250)

    app.layout = html.Div(
        [
            dcc.Graph(
                figure=graph,
                config={"displayModeBar": False},
                style={"width": "100%", "height": "250px"},
            ),
        ],
        style={"width": "100%", "height": "250px"},
    )


def graph_gauge_value(app_name, value, label, size=180, color="#33bbff"):
    """Create Dashboard application for showing a gauge graphic for the
    unused fields
    """
    app = DjangoDash(app_name, external_stylesheets=[dbc.themes.BOOTSTRAP])

    app.layout = html.Div(
        daq.Gauge(
            showCurrentValue=True,
            color=color,
            id="n_used_fields",
            label={"label": label, "style": {"font-size": "1.40rem", "color": "green"}},
            labelPosition="bottom",
            value=value,
            max=((value // 10) + 1) * 10,
            min=0,
            size=size,
        ),
        style={"bottom": 0, "pading-bottom": "30%"},
    )


def bar_graphic(data, col_names, legend, yaxis, options):
    """Options fields are: title, height"""
    if "colors" in options:
        colors = options["colors"]
    else:
        colors = ["#0099ff", "#1aff8c", "#ffad33", "#ff7733", "#66b3ff", "#66ffcc"]
    fig = go.Figure()
    for idx in range(1, len(col_names)):
        fig.add_trace(
            go.Bar(
                x=data[col_names[0]],
                y=data[col_names[idx]],
                name=legend[idx - 1],
                marker_color=colors if "colors" in options else colors[idx - 1],
            )
        )

    # Customize aspect
    fig.update_traces(
        marker_line_color="rgb(8,48,107)",
        marker_line_width=1.5,
        opacity=0.6,
    )
    fig.update_layout(
        title=options["title"],
        title_font_color="green",
        title_font_size=20,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=-45,
        yaxis=yaxis,
        margin=dict(l=0, r=0, t=30, b=0),
        height=options["height"],
    )
    if "xaxis_tics" in options:
        fig.update_layout(xaxis=options["xaxis"])

    plot_div = plot(fig, output_type="div", config={"displaylogo": False})

    return plot_div


def line_graphic(x_data, y_data, options):
    # Create line
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_data, y=y_data, mode="lines", name="lines"))

    fig.update_layout(
        height=options["height"],
        width=options["width"],
        xaxis_title=options["x_title"],
        yaxis_title=options["y_title"],
        margin=dict(t=30, b=0, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=options["title"],
        title_font_color="green",
        title_font_size=20,
    )
    plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    return plot_div


def pie_graphic(labels, values, options, show_legend=True):
    colors = ["#0099ff", "#1aff8c", "#ffad33", "#ff7733", "#66b3ff", "#66ffcc"]
    fig = go.Figure(
        data=go.Pie(
            labels=labels,
            values=values,
        )
    )

    fig.update_traces(
        hoverinfo="label+percent",
        textinfo="value",
        textfont_size=16,
        title_font=dict(size=18, family="Verdana", color="darkgreen"),
        marker=dict(colors=colors, line=dict(color="darkblue", width=1)),
        opacity=0.6,
    )

    fig.update_layout(
        height=320,
        width=320,
        showlegend=show_legend,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=options["title"],
        title_font_color="green",
        title_font_size=20,
    )
    plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    return plot_div


def box_plot_graphic(data, options):
    fig = go.Figure()
    for box_data in data:
        for key, values in box_data.items():
            fig.add_trace(go.Box(y=values, name=key))

    fig.update_layout(
        height=options["height"],
        width=options["width"],
        showlegend=False,
        margin=dict(t=30, b=0, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=-45,
        title=options["title"],
        title_font_color="green",
        title_font_size=20,
    )
    plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    return plot_div

def ridge_plot_graphic(data, options):
    samples = []
    labels = []

    for box_data in data:
        for key, values in box_data.items():
            values = np.array(values, dtype=float)
            samples.append(values)
            labels.append(key)


    fig = ridgeplot(
        samples=samples,  
        bandwidth=4,  
        kde_points=np.linspace(
            np.nanmin(np.concatenate(samples)),  
            np.nanmax(np.concatenate(samples)), 
            500
        ),
        colormode="row-index",
        opacity=0.6,
        labels=labels,
        spacing=5 / 9, 
    )

    fig.update_layout(
        autosize=True,
        title=options["title"],
        font_size=16,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
    )

    plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    return plot_div