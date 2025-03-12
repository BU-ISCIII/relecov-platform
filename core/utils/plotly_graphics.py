# Generic imports
import time
from plotly.offline import plot
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
import dash
from dash import dcc, html
from django_plotly_dash import DjangoDash
from dash.dependencies import Input, Output


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
        fig = log_ydata_if_needed(fig, data[col_names[idx]], ratio=100)

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
    log_ydata_if_needed(fig, y_data, ratio=100)
    if "xaxis" in options:
        fig.update_layout(xaxis=options["xaxis"])
    plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    return plot_div


def histogram_graphic(data, col_names, options):
    graph = px.bar(
        data, y=col_names[1], x=col_names[0], text_auto=True, width=options["width"]
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
    ydata = data[col_names[1]]
    graph = log_ydata_if_needed(graph, ydata, ratio=100)

    plot_div = plot(graph, output_type="div", config={"displaylogo": False})
    return plot_div


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
    graph.update_layout(margin=dict(t=20, b=10, l=20, r=30))
    plot_div = plot(graph, output_type="div", config={"displaylogo": False})
    return plot_div


# FIXME: This function es never called within the platform
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
        title=title,
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


def pie_graphic(data, names, title, show_legend=False):
    colors = [
        "cyan",
        "red",
        "gold",
        "darkblue",
        "darkred",
        "magenta",
        "darkorange",
        "turquoise",
    ]
    fig = go.Figure(
        data=go.Pie(
            labels=names,
            values=data,
        )
    )
    fig.update_traces(
        title=title,
        title_font=dict(size=15, family="Verdana", color="darkgreen"),
        marker=dict(colors=colors, line=dict(color="black", width=1)),
    )
    fig.update_layout(
        height=350, width=270, showlegend=show_legend, margin=dict(t=0, b=0, l=0, r=0)
    )
    plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    return plot_div


def needle_plot(mdata):
    """Create a needleplot using dash that represents mutations along some
    genomic regions.
    """
    mdata = mdata.copy()
    mdata["x"] = [int(x) for x in mdata["x"]]
    app = DjangoDash("sampleVariantGraphic", serve_locally=True)
    app.layout = html.Div(
        children=[
            html.Div(
                children=[
                    html.Div(
                        [
                            "Show Range Slider",
                            dcc.Checklist(
                                id="toggle-rangeslider",
                                options=[{"label": "Enable", "value": "on"}],
                                value=["on"],
                                inline=True,
                            ),
                        ],
                        style={"margin-left": "20px"},
                    ),
                    html.Div(
                        children=[
                            dcc.Markdown(
                                id="samples_markdown",
                            )
                        ],
                        style={"margin-left": "50px"},
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "start",
                    "align-items": "flex-start",
                },
            ),
            html.Div(
                children=[
                    dcc.Loading(
                        id="loading_plot_wrapper",
                        type="default",
                        children=[
                            html.Div(
                                id="needleplot-container-div",
                                children=[
                                    dcc.Store(id="mdata-store", data=mdata),
                                    dcc.Graph(
                                        id="needleplot-graph",
                                        style={"padding-top": "15px"},
                                    ),
                                ],
                                style={"position": "relative"},
                            )
                        ],
                        overlay_style={"visibility": "visible", "filter": "blur(1px)"},
                        parent_style={"position": "relative"},
                    ),
                    dcc.Store(
                        id="previous-data",
                        storage_type="memory",
                        data={"first_load": True},
                    ),
                ],
            ),
        ]
    )

    @app.callback(
        [
            Output("needleplot-graph", "figure"),
            Output("samples_markdown", "children"),
            Output("previous-data", "data"),
        ],  # Track loading state
        [
            Input("mdata-store", "data"),
            Input("toggle-rangeslider", "value"),
            Input("needleplot-graph", "relayoutData"),
            Input("previous-data", "data"),
        ],
        prevent_initial_call=True,  # Avoid triggering on page load
    )
    def update_sample(mdata, toogle_rangeslider, relayout_data, prev_data):
        current_time = time.time()
        first_load = prev_data["first_load"]
        next_data = {}
        if not relayout_data:
            next_data["prev_relayout"] = relayout_data
        if not first_load:
            last_time = prev_data["last_update"]
            # Dont update if no relayout_data is returned from rangeslider
            if not relayout_data or not relayout_data.get("xaxis.range", []):
                print("No valid relayout data found")
                raise dash.exceptions.PreventUpdate
            # Compare current relayoutData with the previous one
            previous_range = prev_data.get("xaxis.range", [])
            current_range = relayout_data.get("xaxis.range", [])
            if previous_range == current_range:
                print("No change in relayoutData, skipping update.")
                raise dash.exceptions.PreventUpdate
            last_time = prev_data["last_update"]
            # Ensure that the last state has not been updated too recently
            if current_time - last_time < 0.25:
                print(f"Did not update. Diff was {time.time() - last_time}")
                raise dash.exceptions.PreventUpdate
        # Update previous relayout data
        next_data["prev_relayout"] = relayout_data
        next_data["first_load"] = False
        # Start updating process
        next_data["last_update"] = current_time
        markdown_text = f"Showing mutations for selected sample"
        # TODO: Include all color mapping dicts for domains and mutation types in graphic_json
        domain_color_map = {
            "orf1ab": "#1f77b4",  # Blue
            "S": "#ff7f0e",  # Orange
            "ORF3a": "#2ca02c",  # Green
            "E": "#d62728",  # Red
            "M": "#9467bd",  # Purple
            "ORF6": "#8c564b",  # Brown
            "ORF7a": "#e377c2",  # Pink
            "ORF7b": "#7f7f7f",  # Gray
            "ORF8": "#bcbd22",  # Yellow-green
            "N": "#17becf",  # Cyan
            "ORF10": "#ffbb78",  # Light orange
        }
        mutation_color_map = {
            "missense_variant": "#E6194B",  # Red
            "Unknown": "#A9A9A9",  # Gray THESE ARE RENAMED FROM NONE VALUES
            "disruptive_inframe_insertion": "#BFEF45",  # Light Green
            "frameshift_variant": "#F58231",  # Orange
            "splice_region_variant&stop_retained_variant": "#FF8DA1",  # Pink
            "conservative_inframe_deletion": "#BF8970",  # Yellow
            "synonymous_variant": "#4363D8",  # Blue
            "stop_lost": "#42D4F4",  # Cyan
            "frameshift_variant&start_lost": "#F032E6",  # Magenta
            "start_lost": "#3CB44B",  # Green
            "disruptive_inframe_deletion": "#D4AF37",  # Light Red
            "gene_fusion": "#469990",  # Teal
            "conservative_inframe_insertion": "#DCBEFF",  # Lavender
            "stop_gained": "#9A6324",  # Brown
            "upstream_gene_variant": "#911EB4",  # Purple
            "frameshift_variant&stop_lost&splice_region_variant": "#800000",  # Dark Red
            "frameshift_variant&stop_gained": "#A65628",  # Dark Brown
            "stop_retained_variant": "#FF6347",  # Tomato Red
            "downstream_gene_variant": "#808000",  # Olive
        }

        # Create NeedlePlot and extract figure
        fig = go.Figure()
        if toogle_rangeslider == ["on"]:
            fig.update_layout(
                xaxis_rangeslider=dict(visible=True, bgcolor="rgba(255, 255, 255, 0)")
            )
        if relayout_data and "xaxis.range" in relayout_data:
            # relayout data listens to updates in the plot from rangeslider
            min_x, max_x = relayout_data["xaxis.range"]
            fig.update_layout(xaxis=dict(range=relayout_data["xaxis.range"]))
        else:
            min_x, max_x = (min(mdata["x"]), max(mdata["x"]))

        # X range will be used to define wether to show genome annotations
        x_range = max_x - min_x

        max_pos = 0
        # Store used annotation possitions to avoid overlap
        used_annotations = []
        all_max_x = max([int(x["coord"].split("-")[1]) for x in mdata["domains"]])
        domain_selectors = [
            dict(
                label="All",
                method="relayout",
                args=[{"xaxis.range": [0, all_max_x]}],
            )
        ]
        # Sort domains based on their starting positions, needed for annotations
        sorted_domains = sorted(
            mdata["domains"], key=lambda x: int(x["coord"].split("-")[0])
        )
        for domain in sorted_domains:
            start, end = map(int, domain["coord"].split("-"))
            domain_selectors.append(
                dict(
                    label=domain["name"],
                    method="relayout",
                    args=[
                        {
                            "xaxis.range": [start, end],
                        }
                    ],
                )
            )
            max_pos = max(max_pos, end)
            fig.add_shape(
                type="rect",
                x0=start,
                x1=end,
                y0=0,
                y1=-0.12,
                fillcolor=domain_color_map.get(domain["name"], "lightgray"),
                opacity=0.3,
                layer="below",
                line=dict(width=0),
            )
            # Define a threshold for spacing relative to the x range. I used 0.04 ad-hoc
            x_space_threshold = x_range * 0.05

            # Determine an appropriate y-level to avoid overlap
            annotation_x = (start + end) / 2  # Place annotation in the middle
            annotation_y = -0.06  # Default y-level

            for prev_x, _ in used_annotations:
                if abs(annotation_x - prev_x) < x_space_threshold:
                    domain["name"] = ""  # Do not show annotation if it would overlap
                    break
            else:
                # Store the adjusted position if the annotation is used
                used_annotations.append((annotation_x, annotation_y))

            # Add text labels for domains
            fig.add_annotation(
                x=annotation_x,
                y=annotation_y,
                text=domain["name"],
                showarrow=False,
                font=dict(size=12, color="black"),
            )
        fig.add_shape(
            type="rect",
            x0=0,
            x1=max_pos,
            y0=0,
            y1=-0.12,
            fillcolor="lightgray",
            opacity=0.3,
            layer="below",
            line=dict(width=0),
        )
        # Filter mutations based on selected range
        filtered_indices = [i for i, x in enumerate(mdata["x"]) if min_x <= x <= max_x]

        filtered_x = [mdata["x"][i] for i in filtered_indices]
        filtered_y = [mdata["y"][i] for i in filtered_indices]
        filtered_mutation_groups = [
            mdata["mutationGroups"][i] for i in filtered_indices
        ]

        mutation_traces = {}
        for x, y, mutation_type in zip(
            filtered_x, filtered_y, filtered_mutation_groups
        ):
            if mutation_type is None:
                mutation_type = "Unknown"
            color = mutation_color_map.get(mutation_type)

            if mutation_type not in mutation_traces:
                mutation_traces[mutation_type] = {
                    "x_points": [],
                    "y_points": [],
                    "x_lines": [],
                    "y_lines": [],
                    "color": color,
                }

            # Add mutation marker
            mutation_traces[mutation_type]["x_points"].append(int(x))
            mutation_traces[mutation_type]["y_points"].append(y)

            # Ensure each line (needle) is positioned at its own location
            mutation_traces[mutation_type]["x_lines"].extend(
                [int(x), int(x), None]
            )  # None for breaks
            mutation_traces[mutation_type]["y_lines"].extend(
                [-0.005, y, None]
            )  # None for breaks

        # Add traces for each mutation type
        for mutation_type, data in mutation_traces.items():
            # Line trace for needles
            fig.add_trace(
                go.Scatter(
                    x=data["x_lines"],
                    y=data["y_lines"],
                    mode="lines",
                    line=dict(color=data["color"], width=1),
                    name=mutation_type,  # Legend entry (same as marker)
                    legendgroup=mutation_type,  # group legend with markers
                    showlegend=False,  # Hide extra legend entry for lines
                )
            )

            # Marker trace for mutation points
            fig.add_trace(
                go.Scatter(
                    x=data["x_points"],
                    y=data["y_points"],
                    mode="markers",
                    marker=dict(size=10, color=data["color"]),
                    legendgroup=mutation_type,  # Group legend with lines
                    name=mutation_type,  # Legend entry
                )
            )
        fig.update_layout(
            title={
                "text": "Needle Plot",
                "x": 0.1,
                "xanchor": "left",
            },
            xaxis=dict(
                title="Genome Position",
                tickmode="auto",
                automargin=True,
                tickformat="d",
                showgrid=False,
                zeroline=False,
                range=[min_x, max_x],
                rangeselector=dict(),
            ),
            paper_bgcolor="white",
            plot_bgcolor="white",
            yaxis_title="Allele Frequency",
            yaxis_range=[-0.12, 1.15],
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    x=0,
                    y=1.15,
                    xanchor="left",
                    showactive=True,
                    buttons=domain_selectors,
                )
            ],
        )
        return fig, markdown_text, next_data

    return app


def log_ydata_if_needed(graph, ydata, ratio=100):
    """Try to apply logaritmic scale to ydata if necessary

    Args:
        graph (plotly.figure): Plotly figure ready to be renderized
        ydata (list): list of values or pandas.series (e.g. df[col])
        ratio (int): ratio threshold to apply log scale or not

    Return:
        graph: Graph with ydata scaled with logarithmic scale
    """
    min_score = min(ydata)
    max_score = max(ydata)
    if min_score == 0:
        drop_0s = [x for x in ydata if x != 0]
        if not drop_0s:  # All data is 0 so do not scale
            return graph
        min_score = min(drop_0s)
    minmax_ratio = max_score / min_score
    if minmax_ratio >= ratio:
        try:
            graph.update_layout(yaxis_type="log", yaxis_dtick=1)
        except TypeError as e:  # Input graph does not accept log scaling
            print(f"ERROR while trying to scale ydata: {e}")
    return graph
