# Generic imports
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.graph_objects as go
from dash import html, dcc
from django_plotly_dash import DjangoDash
from plotly.offline import plot
from ridgeplot import ridgeplot
import numpy as np
import pandas as pd
import re
from textwrap import wrap as text_wrap



def format_labels(labels, wrap=None, truncate=None, separator="..."):
    """
    Formats labels by applying word wrapping and/or truncation.

    Parameters:
        labels (list): List of text labels to format.
        wrap (int, optional): Max length before wrapping text into new lines.
        truncate (int, optional): Max length before truncating text.
        separator (str, optional): Separator for truncated text, default "...".

    Returns:
        tuple: (formatted_labels, hover_labels)
            - formatted_labels: Labels modified for display.
            - hover_labels: Original labels for hover (useful when truncated).
    """
    formatted_labels = []
    hover_labels = []

    for label in labels:
        original_label = label

        if truncate and len(label) > truncate:
            words = re.split(r'[\s_]', label)
            if len(words) == 1:
                label = label[: truncate - len(separator)] + separator
            else:
                first_part = words[0][: truncate // 2]
                last_part = words[-1][-truncate // 2 :]
                label = f"{first_part}{separator}{last_part}<span style='display:none'>_{hash(original_label)}</span>"

        elif wrap and len(label) > wrap:
            label = "<br>".join(text_wrap(label, wrap))

        formatted_labels.append(label)
        hover_labels.append(original_label)

    return formatted_labels, hover_labels


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

    labels = data[col_names[0]]
    wrap_length = options.get("wrap_labels")
    truncate_length = options.get("truncate_labels")

    formatted_labels, hover_labels = format_labels(
        labels, wrap=wrap_length, truncate=truncate_length
    )

    fig = go.Figure()
    for idx in range(1, len(col_names)):
        values = data[col_names[idx]]
        fig.add_trace(
            go.Bar(
                x=formatted_labels,
                y=values,
                name=legend[idx - 1],
                marker_color=colors if "colors" in options else colors[idx - 1],
                customdata=list(zip(hover_labels, [col_names[idx]] * len(values))),
                hovertemplate="<b>%{customdata[0]}</b><br>"
                              "%{customdata[1]}: %{y}<br>"
                              "<extra></extra>",
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
        xaxis=dict(options.get("xaxis", {})),
    )
    
    if "wrap_labels" in options or "truncate_labels" in options:
        fig.update_xaxes(ticktext=formatted_labels)

    if "xaxis_tics" in options:
        fig.update_layout(xaxis=options["xaxis"])

    plot_div = plot(fig, output_type="div", config={"displaylogo": False})

    return plot_div


def line_graphic(x_data, y_data, options):
    # Create line
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_data, y=y_data, mode="lines", name="lines"))

    fig.update_layout(
        autosize=True,
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
    
    wrap_length = options.get("wrap_labels")
    truncate_length = options.get("truncate_labels")
    
    fig = go.Figure()
    formatted_labels = [] 
    colors = {}
    for box_data in data:
        for key, values in box_data.items():
            if not values: 
                continue

            values = np.array(values)  

            if values.size == 0:
                continue
            min_val, q1, median, q3, max_val = np.min(values), np.percentile(values, 25), np.median(values), np.percentile(values, 75), np.max(values)
            
            formatted_label, hover_label = format_labels([key], wrap=wrap_length, truncate=truncate_length)
            full_label = key
            formatted_labels.append(formatted_label[0])
            
            if key not in colors:
                colors[key] = f"rgba({np.random.randint(50, 200)}, {np.random.randint(50, 200)}, {np.random.randint(50, 200)}, 0.6)"  

            
            fig.add_trace(go.Box(
                y=values,
                name=formatted_label[0],
                boxmean=True,
                jitter=0.4,
                boxpoints='all',
                pointpos=0,
                marker=dict(
                    size=3,
                    opacity=0.25
                ),
                marker_color=colors[key],
                hoverinfo="skip"
                ))
            fig.add_trace(go.Scatter(
                x=[formatted_label[0]] * len(values),
                y=values,
                mode="markers",
                marker=dict(color=colors[key], opacity=0), 
                customdata=[[hover_label[0], min_val, q1, median, q3, max_val]] * len(values),
                hovertemplate="<b>%{customdata[0]}</b><br>"
                              "Min: %{customdata[1]:.2f}<br>"
                              "Q1: %{customdata[2]:.2f}<br>"
                              "Median: %{customdata[3]:.2f}<br>"
                              "Q3: %{customdata[4]:.2f}<br>"
                              "Max: %{customdata[5]:.2f}<br>"
                              "<extra></extra>",
            ))
            
    
    if wrap_length or truncate_length:
        fig.update_xaxes(ticktext=formatted_labels)
    
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
            np.nanmin(np.concatenate(samples)), np.nanmax(np.concatenate(samples)), 500
        ),
        colormode="row-index",
        opacity=0.6,
        labels=labels,
        spacing=5 / 9,
    )

    fig.update_layout(
        autosize=True,
        title=options["title"],
        title_font_color="green",
        title_font_size=20,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="",
        yaxis_title="",
        showlegend=False,
    )

    plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    return plot_div


def box_plot_graphic_bins(x_data, y_data, options):
    df = pd.DataFrame({"Depth": x_data, "Samples": y_data})

    bins = [0, 100, 500, 1000, 2000, 3000, 5000, float("inf")]
    labels = [
        "0-100",
        "100-500",
        "500-1000",
        "1000-2000",
        "2000-3000",
        "3000-5000",
        ">5000",
    ]
    df["Depth Group"] = pd.cut(df["Depth"], bins=bins, labels=labels)

    fig = go.Figure()

    for label in labels:
        subset = df[df["Depth Group"] == label]
        if not subset.empty:
            fig.add_trace(
                go.Box(
                    y=subset["Samples"],
                    name=label,
                    boxmean=True,
                    marker_color="blue",
                )
            )

    fig.update_layout(
        autosize=True,
        showlegend=False,
        margin=dict(t=30, b=30, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title=options["x_title"],
        yaxis_title=options["y_title"],
        title=options["title"],
        title_font_color="green",
        title_font_size=20,
    )

    plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    return plot_div
