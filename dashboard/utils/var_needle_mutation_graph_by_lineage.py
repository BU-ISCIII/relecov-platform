# Generic imports
import time
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from django_plotly_dash import DjangoDash

# Local imports
import dashboard.utils.generic_graphic_data
import dashboard.utils.generic_process_data


def get_variant_data_from_lineages(graphic_name=None, lineage=None, chromosome=None):
    json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(graphic_name)

    if json_data is None:
        # Execute the pre-processed task to get the data
        result = dashboard.utils.generic_process_data.pre_proc_variations_per_lineage(
            chromosome
        )
        if "ERROR" in result:
            return result

    json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(graphic_name)
    # Return None to indicate that there is no data stored yet
    if json_data is None:
        return None, None, None

    if lineage is None:
        lineage = sorted(list(json_data.keys()))[0]
    mdata = json_data[lineage]
    n_samples = mdata["SamplesWithLineage"]
    return mdata, lineage, n_samples


def create_needle_plot_graph_mutation_by_lineage(
    lineage_list, lineage, mdata, n_samples
):
    options = []
    for lin in lineage_list:
        options.append({"label": lin, "value": lin})

    mdata["x"] = [int(x) for x in mdata["x"]]
    app = DjangoDash("needlePlotMutationByLineage", serve_locally=True)
    app.layout = html.Div(
        children=[
            html.Div(
                children=[
                    html.Div(
                        children=[
                            "Select Lineage",
                            dcc.Dropdown(
                                id="needleplot-select-lineage",
                                options=options,
                                clearable=False,
                                multi=False,
                                value=lineage,
                                style={"width": "150px", "margin-right": "30px"},
                            ),
                        ],
                        style={"margin-left": "20px"},
                    ),
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
                                children=f"Showing mutations for {n_samples} samples",
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
                                    dcc.Graph(
                                        id="needleplot-graph",
                                        style={"padding-top": "15px"},
                                    ),
                                    dcc.Store(
                                        id="debounced-relayout", storage_type="memory"
                                    ),
                                    dcc.Store(
                                        id="relayout-timestamp", storage_type="memory"
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
        Output("relayout-timestamp", "data"),
        Output("debounced-relayout", "data"),
        Input("needleplot-graph", "relayoutData"),
        State("relayout-timestamp", "data"),
        prevent_initial_call=True,
    )
    def debounce_relayout(relayout_data, last_timestamp):
        now = time.time()
        if last_timestamp is None or now - last_timestamp > 0.4:
            return now, relayout_data
        raise dash.exceptions.PreventUpdate

    @app.callback(
        Output("needleplot-graph", "figure"),
        Output("samples_markdown", "children"),
        Input("debounced-relayout", "data"),
        Input("needleplot-select-lineage", "value"),
        Input("toggle-rangeslider", "value"),
        prevent_initial_call=True,
    )
    def update_sample(relayout_data, selected_lineage, toogle_rangeslider):
        mdata, _, n_samples = get_variant_data_from_lineages(
            graphic_name="variations_per_lineage",
            lineage=selected_lineage,
            chromosome=None,
        )
        mdata["x"] = [int(x) for x in mdata["x"]]
        markdown_text = f"Showing mutations for {n_samples} samples"
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

    return app
