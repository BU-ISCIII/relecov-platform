from plotly.offline import plot

import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff


def histogram_graphic(data, col_names, option):

    graph = px.bar(data, y=col_names[1], x=col_names[0], text_auto=True)
    # Customize aspect
    graph.update_traces(
        marker_color="rgb(158,202,225)",
        marker_line_color="rgb(8,48,107)",
        marker_line_width=1.5,
        opacity=0.6,
    )
    graph.update_layout(title=option["title"], xaxis_tickangle=-45)

    plot_div = plot(graph, output_type="div")

    return plot_div


def pie_graphic(d_frame, option):
    return


def gauge_graphic(data):
    graph = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=data["value"],
            number={"suffix": "%"},
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Samples Analized in percentage"},
            gauge={"axis": {"range": [None, 100]}},
        )
    )
    plot_div = plot(graph, output_type="div")

    return plot_div


def bullet_graphic(value, title):
    point = str(value)
    top_value = int(value)
    data = [
        {
            "label": "Upload %",
            "range": [40, 70, 100],
            "performance": [40, top_value],
            "point": [point],
        }
    ]

    measure_colors = ["rgb(68, 107, 162)", "rgb(0, 153, 0)"]
    fig = ff.create_bullet(
        data,
        titles="label",
        title="",
        markers="point",
        measures="performance",
        ranges="range",
        orientation="v",
        measure_colors=measure_colors,
        margin=dict(
            t=25,
            r=0,
            b=0,
            l=0,
        ),
    )
    fig.update_layout(height=450, width=330)
    plot_div = plot(fig, output_type="div")
    return plot_div
