# Generic imports
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Local imports
import dashboard.utils.generic_graphic_data
import dashboard.utils.generic_process_data


def load_variant_graphic_dataframe():
    json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
        "variant_graphic_data"
    )
    if json_data is None:
        result = dashboard.utils.generic_process_data.pre_proc_variant_graphic()
        if "ERROR" in result:
            return result
        json_data = dashboard.utils.generic_graphic_data.get_graphic_json_data(
            "variant_graphic_data"
        )

    data_df = pd.DataFrame(json_data).dropna()
    if data_df.empty:
        return data_df

    data_df["Collection date"] = pd.to_datetime(data_df["Collection date"])
    data_df = data_df[data_df["Collection date"] >= "2020-01-01"]
    data_df["samples"] = data_df["samples"].astype(int)
    return data_df.sort_values("Collection date")


def prepare_variant_graphic_dataframe(data_df):
    data_week_df = (
        data_df.groupby(["Lineage", pd.Grouper(key="Collection date", freq="W-MON")])[
            "samples"
        ]
        .sum()
        .reset_index()
        .sort_values("Collection date")
    )

    full_weeks_as_str = pd.date_range(
        data_week_df["Collection date"].min(),
        data_week_df["Collection date"].max(),
        freq="W-MON",
    ).strftime("%G-W%V-%u")

    df_full = pd.MultiIndex.from_product(
        [data_week_df["Lineage"].unique(), full_weeks_as_str],
        names=["Lineage", "Collection date"],
    ).to_frame(index=False)
    df_full["Collection date"] = pd.to_datetime(
        df_full["Collection date"], format="%G-W%V-%u"
    )

    df_full = df_full.merge(
        data_week_df, on=["Lineage", "Collection date"], how="left"
    ).fillna(0)
    df_full["samples"] = df_full["samples"].astype(int)
    return df_full


def build_lineage_variation_figure(df_full, start_date=None, end_date=None):
    lineages = df_full["Lineage"].unique().tolist()
    first_date = df_full["Collection date"].min()
    last_date = df_full["Collection date"].max()

    if start_date is None or end_date is None:
        sub_data_df = df_full.loc[
            (df_full["Collection date"] >= first_date)
            & (df_full["Collection date"] < last_date)
        ].copy()
    else:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        sub_data_df = df_full.loc[
            (df_full["Collection date"] >= start_date_obj)
            & (df_full["Collection date"] < end_date_obj)
        ].copy()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    if sub_data_df.empty:
        fig.add_trace(go.Scatter())
        fig.add_annotation(
            text="No samples found for the selected dates",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=20, color="red"),
        )
        fig.update_layout(
            xaxis=dict(showline=True, linecolor="black", linewidth=2, mirror=True),
            yaxis=dict(showline=True, linecolor="black", linewidth=2, mirror=True),
            barmode="stack",
            hovermode="x unified",
            legend_xanchor="center",
            legend_yanchor="top",
            legend_orientation="h",
            legend_x=0.5,
            legend_y=-0.30,
            bargap=0,
            bargroupgap=0,
            margin_l=10,
            margin_r=10,
            margin_b=40,
            margin_t=40,
            height=600,
            paper_bgcolor="white",
            plot_bgcolor="white",
        )
        return fig

    sub_data_df["Collection ISOWeek"] = sub_data_df["Collection date"].dt.strftime(
        "%Y-W%V"
    )

    graph_df = sub_data_df.pivot_table(
        index="Collection ISOWeek",
        columns="Lineage",
        values="samples",
        aggfunc="sum",
        fill_value=0,
    )
    graph_df = graph_df.fillna(0)
    graph_df[lineages] = graph_df[lineages].astype(int)
    value_per_df = (graph_df.div(graph_df.sum(axis=1), axis=0) * 100).round(2)
    value_per_df = value_per_df.fillna(0)
    samples_per_week = graph_df.sum(axis=1)

    hover_text = [f"{y}" for y in samples_per_week.values]
    fig.add_trace(
        go.Scatter(
            x=value_per_df.index,
            y=samples_per_week,
            hoverinfo="text",
            hovertemplate="%{text}",
            mode="lines",
            name="Number of samples",
            line_color="#0066cc",
            line_width=2,
            text=hover_text,
        ),
        secondary_y=True,
    )
    for lineage in lineages:
        hover_text = [
            (
                f"<b>{lineage}: {y}%</b><extra></extra>"
                if y > 0
                else f"{lineage}: {y}%<extra></extra>"
            )
            for y in value_per_df[lineage].values
        ]
        fig.add_trace(
            go.Scatter(
                x=value_per_df.index,
                y=value_per_df[lineage],
                hoverinfo="text",
                hovertemplate="%{text}",
                mode="lines",
                name=lineage,
                opacity=0.7,
                stackgroup="variants",
                text=hover_text,
            ),
            secondary_y=False,
        )

    fig.update_xaxes(title="Collection Date (ISOweeks)")
    fig.update_yaxes(range=[0, 100], title_text="<b>Lineage % relative", secondary_y=False)
    fig.update_yaxes(
        title_text="<b>Number of samples processed</b>", secondary_y=True
    )
    fig.update_layout(
        title_text="Variants over the selected period",
        autotypenumbers="convert types",
        barmode="stack",
        hovermode="x unified",
        legend_xanchor="center",
        legend_yanchor="top",
        legend_orientation="h",
        legend_x=0.5,
        legend_y=-0.30,
        bargap=0,
        bargroupgap=0,
        margin_l=10,
        margin_r=10,
        margin_b=40,
        margin_t=40,
        height=600,
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(showline=True, linecolor="black", linewidth=2, mirror=True),
        yaxis=dict(
            showline=True,
            linecolor="black",
            linewidth=2,
            mirror=True,
            ticksuffix=" ",
        ),
        yaxis2_tickprefix=" ",
    )
    return fig


def create_lineages_variations_graphic():
    data_df = load_variant_graphic_dataframe()
    if isinstance(data_df, dict) and "ERROR" in data_df:
        return data_df
    if data_df.empty:
        return {"ERROR": "No lineage data available"}
    return {"OK": True}
