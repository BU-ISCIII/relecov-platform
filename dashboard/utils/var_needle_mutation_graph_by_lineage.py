# Generic imports
import plotly.graph_objects as go

# Local imports
import dashboard.utils.generic_graphic_data
import dashboard.utils.generic_process_data


APP_NAME = "needlePlotMutationByLineage"


def get_variant_data_from_lineages(graphic_name=None, lineage=None, chromosome=None):
    json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(graphic_name)

    if json_data is None:
        result = dashboard.utils.generic_process_data.pre_proc_variations_per_lineage(
            chromosome
        )
        if "ERROR" in result:
            return result

    json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(graphic_name)
    if json_data is None:
        return None, None, None

    if lineage is None:
        lineage = sorted(list(json_data.keys()))[0]
    mdata = json_data[lineage]
    n_samples = mdata["SamplesWithLineage"]
    return mdata, lineage, n_samples


def empty_needle_plot_figure():
    fig = go.Figure()
    fig.update_layout(
        title={"text": "Needle Plot", "x": 0.1, "xanchor": "left"},
        xaxis_title="Genome Position",
        yaxis_title="Population Allele Frequency",
        paper_bgcolor="white",
        plot_bgcolor="white",
        yaxis_range=[-0.12, 1.15],
    )
    return fig


def build_needle_plot_initial_arguments(lineage_list, lineage):
    options = [{"label": lin, "value": lin} for lin in lineage_list]
    return {
        "needleplot-select-lineage": {"options": options, "value": lineage},
        "toggle-rangeslider": {"value": ["on"]},
    }


def build_needle_plot_figure(selected_lineage, toggle_rangeslider=None, relayout_data=None):
    mdata, _, n_samples = get_variant_data_from_lineages(
        graphic_name="variations_per_lineage",
        lineage=selected_lineage,
        chromosome=None,
    )
    if not mdata or not mdata.get("x"):
        return empty_needle_plot_figure(), "No lineage mutations available"

    mdata = dict(mdata)
    mdata["x"] = [int(x) for x in mdata["x"]]
    markdown_text = f"Showing mutations for {n_samples} samples"
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

    fig = go.Figure()
    if toggle_rangeslider == ["on"]:
        fig.update_layout(
            xaxis_rangeslider=dict(visible=True, bgcolor="rgba(255, 255, 255, 0)")
        )
    if relayout_data and "xaxis.range" in relayout_data:
        min_x, max_x = relayout_data["xaxis.range"]
        fig.update_layout(xaxis=dict(range=relayout_data["xaxis.range"]))
    else:
        min_x, max_x = (min(mdata["x"]), max(mdata["x"]))

    x_range = max_x - min_x if max_x > min_x else 1
    max_pos = 0
    used_annotations = []
    all_max_x = max([int(x["coord"].split("-")[1]) for x in mdata["domains"]])
    domain_selectors = [
        dict(label="All", method="relayout", args=[{"xaxis.range": [0, all_max_x]}])
    ]
    sorted_domains = sorted(mdata["domains"], key=lambda x: int(x["coord"].split("-")[0]))
    for domain in sorted_domains:
        start, end = map(int, domain["coord"].split("-"))
        domain_selectors.append(
            dict(label=domain["name"], method="relayout", args=[{"xaxis.range": [start, end]}])
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

    filtered_indices = [i for i, x in enumerate(mdata["x"]) if min_x <= x <= max_x]
    filtered_x = [mdata["x"][i] for i in filtered_indices]
    filtered_y = [mdata["y"][i] for i in filtered_indices]
    filtered_mutation_groups = [mdata["mutationGroups"][i] for i in filtered_indices]

    mutation_traces = {}
    for x, y, mutation_type in zip(filtered_x, filtered_y, filtered_mutation_groups):
        if mutation_type is None:
            mutation_type = "Unknown"
        color = mutation_color_map.get(mutation_type, "#6c757d")

        if mutation_type not in mutation_traces:
            mutation_traces[mutation_type] = {
                "x_points": [],
                "y_points": [],
                "x_lines": [],
                "y_lines": [],
                "color": color,
            }

        mutation_traces[mutation_type]["x_points"].append(int(x))
        mutation_traces[mutation_type]["y_points"].append(y)
        mutation_traces[mutation_type]["x_lines"].extend([int(x), int(x), None])
        mutation_traces[mutation_type]["y_lines"].extend([-0.005, y, None])

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
        yaxis_title="Population Allele Frequency",
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
    return fig, markdown_text


def create_needle_plot_graph_mutation_by_lineage(lineage_list, lineage, mdata, n_samples):
    if not mdata:
        return {"ERROR": "No lineage mutation data available"}
    return build_needle_plot_initial_arguments(lineage_list, lineage)
