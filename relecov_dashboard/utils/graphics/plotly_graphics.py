from plotly.offline import plot
import plotly.graph_objects as go

import dash_bootstrap_components as dbc
from dash import html
import dash_daq as daq
from django_plotly_dash import DjangoDash


def graph_gauge_percent_values(app_name, value, label, size=180):
    """Create Dashboard application for showing a gauge graphic for the
    percentage  values
    """
    app = DjangoDash(app_name, external_stylesheets=[dbc.themes.BOOTSTRAP])
    if value <= 40:
        text_color = "red"
    elif value <= 75:
        text_color = "#e6e600"
    else:
        text_color = "green"
    app.layout = html.Div(
        daq.Gauge(
            showCurrentValue=True,
            color={
                "default": text_color,
                "gradient": True,
                "ranges": {"red": [0, 40], "yellow": [40, 80], "green": [80, 100]},
            },
            id="my-gauge-1",
            label={"label": label, "style": {"font-size": "1.40rem", "color": "green"}},
            labelPosition="bottom",
            value=value,
            max=100,
            min=0,
            size=size,
        ),
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
                marker_color=colors if "colors" in options else colors[idx - 1]
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
