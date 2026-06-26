# Generic imports
from plotly.offline import plot
import plotly.graph_objects as go
import plotly.express as px

COLOR_PALETTE = [
    "#448873",
    "#809dd4",
    "#99b4c7",
    "#6ca0c4",
    "#649d68",
    "#7c8fb2",
    "#828b3c",
    "#45777c",
    "#73423f",
    "#46523a",
]

mi_template = go.layout.Template(
    layout=dict(
        paper_bgcolor="#f8f9fc",
        plot_bgcolor="#f8f9fc",
        font=dict(family="Oxanium, sans-serif", color="#042940"),
        xaxis=dict(
            color="#042940",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.6)",
            gridwidth=1.5,
            automargin=True,
            title_standoff=10,
            zeroline=False,
        ),
        yaxis=dict(
            color="#042940",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.6)",
            gridwidth=1.5,
            automargin=True,
            title_standoff=10,
            zeroline=False,
        ),
        legend=dict(font=dict(color="#042940"), bgcolor="rgba(0,0,0,0)"),
        title=dict(font=dict(color="#042940"), x=0.01, xanchor="left"),
    )
)


def bar_graphic(data, col_names, legend, yaxis, options):
    """Options fields are: title, height"""
    if "colors" in options:
        colors = options["colors"]
    else:
        colors = COLOR_PALETTE
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
    fig.update_layout(
        title=options["title"],
        template=mi_template,
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
    marker_color = options.get("line_color", COLOR_PALETTE[1])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=y_data,
            mode="lines",
            name="lines",
            line=dict(color=marker_color),
        )
    )

    fig.update_layout(
        height=options["height"],
        width=options["width"],
        xaxis_title=options["x_title"],
        yaxis_title=options["y_title"],
        margin=dict(t=30, b=0, l=0, r=0),
        template=mi_template,
        title=options["title"],
    )
    log_ydata_if_needed(fig, y_data, ratio=100)
    if "xaxis" in options:
        fig.update_layout(xaxis=options["xaxis"])
    plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    return plot_div


def histogram_graphic(data, col_names, options):
    colors = COLOR_PALETTE
    graph = px.bar(
        data, y=col_names[1], x=col_names[0], text_auto=True, width=options["width"]
    )
    # Customize aspect
    graph.update_traces(
        marker=dict(color=colors[1]),
        opacity=0.6,
    )
    graph.update_layout(
        title=options["title"],
        template=mi_template,
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


def pie_graphic(data, names, title, show_legend=False):
    colors = COLOR_PALETTE
    fig = go.Figure(
        data=go.Pie(
            labels=names,
            values=data,
        )
    )
    fig.update_traces(
        title=title,
        hoverinfo="label+percent",
        textinfo="value",
        textfont_size=16,
        title_font=dict(size=18, family="Oxanium, sans-serif", color="#448873"),
        marker=dict(colors=colors),
        opacity=0.6,
    )
    fig.update_layout(
        height=350,
        width=270,
        showlegend=show_legend,
        margin=dict(t=0, b=0, l=0, r=0),
        template=mi_template,
    )
    plot_div = plot(fig, output_type="div", config={"displaylogo": False})
    return plot_div


def empty_sample_variant_figure():
    fig = go.Figure()
    fig.update_layout(
        title="No variants available for the selected sample",
        template=mi_template,
        xaxis_title="Genome Position",
        yaxis_title="Allele Frequency",
        paper_bgcolor="white",
        plot_bgcolor="white",
        yaxis_range=[-0.12, 1.15],
    )
    return fig


def build_sample_variant_initial_arguments(mdata):
    normalized = {
        "x": [int(x) for x in mdata.get("x", []) if x is not None],
        "y": list(mdata.get("y", [])),
        "mutationGroups": list(mdata.get("mutationGroups", [])),
        "domains": list(mdata.get("domains", [])),
    }
    return {
        "mdata-store": {"data": normalized},
        "toggle-rangeslider": {"value": ["on"]},
        "previous-data": {"data": {"first_load": True}},
    }


def build_sample_variant_figure(mdata, toggle_rangeslider=None, relayout_data=None):
    if not mdata or not mdata.get("x"):
        return empty_sample_variant_figure()

    domain_color_map = {
        "orf1ab": "#1f77b4",
        "S": "#ff7f0e",
        "ORF3a": "#2ca02c",
        "E": "#d62728",
        "M": "#9467bd",
        "ORF6": "#8c564b",
        "ORF7a": "#e377c2",
        "ORF7b": "#7f7f7f",
        "ORF8": "#bcbd22",
        "N": "#17becf",
        "ORF10": "#ffbb78",
    }
    mutation_color_map = {
        "missense_variant": "#E6194B",
        "Unknown": "#A9A9A9",
        "disruptive_inframe_insertion": "#BFEF45",
        "frameshift_variant": "#F58231",
        "splice_region_variant&stop_retained_variant": "#FF8DA1",
        "conservative_inframe_deletion": "#BF8970",
        "synonymous_variant": "#4363D8",
        "stop_lost": "#42D4F4",
        "frameshift_variant&start_lost": "#F032E6",
        "start_lost": "#3CB44B",
        "disruptive_inframe_deletion": "#D4AF37",
        "gene_fusion": "#469990",
        "conservative_inframe_insertion": "#DCBEFF",
        "stop_gained": "#9A6324",
        "upstream_gene_variant": "#911EB4",
        "frameshift_variant&stop_lost&splice_region_variant": "#800000",
        "frameshift_variant&stop_gained": "#A65628",
        "stop_retained_variant": "#FF6347",
        "downstream_gene_variant": "#808000",
    }

    x_values = [int(x) for x in mdata.get("x", [])]
    y_values = list(mdata.get("y", []))
    mutation_groups = list(mdata.get("mutationGroups", []))
    domains = [dict(domain) for domain in mdata.get("domains", [])]
    max_len = min(len(x_values), len(y_values), len(mutation_groups))
    x_values = x_values[:max_len]
    y_values = y_values[:max_len]
    mutation_groups = mutation_groups[:max_len]

    fig = go.Figure()
    if toggle_rangeslider == ["on"]:
        fig.update_layout(
            xaxis_rangeslider=dict(visible=True, bgcolor="rgba(255, 255, 255, 0)")
        )
    if relayout_data and "xaxis.range" in relayout_data:
        min_x, max_x = relayout_data["xaxis.range"]
        fig.update_layout(xaxis=dict(range=relayout_data["xaxis.range"]))
    else:
        min_x, max_x = (min(x_values), max(x_values))

    x_range = max_x - min_x if max_x > min_x else 1
    max_pos = 0
    used_annotations = []
    all_max_x = (
        max([int(x["coord"].split("-")[1]) for x in domains]) if domains else max_x
    )
    domain_selectors = [
        dict(
            label="All",
            method="relayout",
            args=[{"xaxis.range": [0, all_max_x]}],
        )
    ]
    sorted_domains = sorted(domains, key=lambda x: int(x["coord"].split("-")[0]))
    for domain in sorted_domains:
        start, end = map(int, domain["coord"].split("-"))
        domain_selectors.append(
            dict(
                label=domain["name"],
                method="relayout",
                args=[{"xaxis.range": [start, end]}],
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
        x_space_threshold = x_range * 0.05
        annotation_x = (start + end) / 2
        annotation_y = -0.06

        for prev_x, _ in used_annotations:
            if abs(annotation_x - prev_x) < x_space_threshold:
                domain["name"] = ""
                break
        else:
            used_annotations.append((annotation_x, annotation_y))

        fig.add_annotation(
            x=annotation_x,
            y=annotation_y,
            text=domain["name"],
            showarrow=False,
            font=dict(family="Oxanium, sans-serif", size=12, color="black"),
        )
    fig.add_shape(
        type="rect",
        x0=0,
        x1=max_pos or max_x,
        y0=0,
        y1=-0.12,
        fillcolor="lightgray",
        opacity=0.3,
        layer="below",
        line=dict(width=0),
    )

    filtered_indices = [i for i, x in enumerate(x_values) if min_x <= x <= max_x]
    mutation_traces = {}
    for idx in filtered_indices:
        mutation_type = mutation_groups[idx] or "Unknown"
        color = mutation_color_map.get(mutation_type, "#6c757d")
        mutation_traces.setdefault(
            mutation_type,
            {
                "x_points": [],
                "y_points": [],
                "x_lines": [],
                "y_lines": [],
                "color": color,
            },
        )
        mutation_traces[mutation_type]["x_points"].append(int(x_values[idx]))
        mutation_traces[mutation_type]["y_points"].append(y_values[idx])
        mutation_traces[mutation_type]["x_lines"].extend(
            [int(x_values[idx]), int(x_values[idx]), None]
        )
        mutation_traces[mutation_type]["y_lines"].extend([-0.005, y_values[idx], None])

    for mutation_type, data in mutation_traces.items():
        fig.add_trace(
            go.Scatter(
                x=data["x_lines"],
                y=data["y_lines"],
                mode="lines",
                line=dict(color=data["color"], width=1),
                name=mutation_type,
                legendgroup=mutation_type,
                showlegend=False,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=data["x_points"],
                y=data["y_points"],
                mode="markers",
                marker=dict(size=10, color=data["color"]),
                legendgroup=mutation_type,
                name=mutation_type,
            )
        )

    fig.update_layout(
        title={"text": "Needle Plot", "x": 0.1, "xanchor": "left"},
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
    return fig


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
