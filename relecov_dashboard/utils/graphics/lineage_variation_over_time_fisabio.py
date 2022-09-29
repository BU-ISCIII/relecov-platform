#! /usr/bin/python

"""
Generate lineage variation over time plot with data selection
"""
# ---------------------------------------------------------------
__author__ = "Alejandro Sanz-Carbonell (FISABIO - RELECOV)"
__credits__ = ["Alejandro Sanz-Carbonel"]
__email__ = "vigilancia_genomica@gva.es"
# ---------------------------------------------------------------

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# from dash import dcc


def select_range_date(start_date, end_date, df):
    """ "
    Select range date
    """
    # Select DataFrame rows between two dates
    mask = (df["sample_collection_date"] > start_date) & (
        df["sample_collection_date"] <= end_date
    )
    df2 = df.loc[mask]
    return df2


def make_lineage_variaton_plot(data, start_date, end_date, select_range, windowSize):
    """
    We are sliding a time window of X days to collect the frequency and relative percentage of the lineages. We record
    how many samples have each lineage, in another similar table we put relative percentage. In another column we will
    store the number of samples that support this value.

    If a temporal window of 7 days is chosen, the first 6 cases are eliminated, if it is for 15 days,
    the first 14 are eliminated, because the first samples would be calculated with less values than the size
    of the temporal window used.
    """
    # data = '/home/warlog/biohackathon/relecov-platform/relecov_dashboard/utils/graphics/fisabio_data.csv'
    # start_date = '2021-01-01'
    # end_date = '2021-12-31'
    # windowSize = 14
    # Load data and add date format to sample_collection_date
    df = pd.read_csv(data)
    df["sample_collection_date"] = pd.to_datetime(
        df["sample_collection_date"], format="%Y-%m-%d"
    )

    # Remove white gaps dates (No whitespace is displayed in Firefox)
    # dt_all = pd.date_range(start=df['sample_collection_date'].iloc[0], end=df['sample_collection_date'].iloc[-1])
    # dt_obs = [d.strftime("%Y-%m-%d") for d in df['sample_collection_date']]
    # dt_breaks = [d for d in dt_all.strftime("%Y-%m-%d").tolist() if not d in dt_obs]

    # rangebreaks=[dict(values=dt_breaks)] # hide dates with no values

    if select_range is True:
        df = select_range_date(start_date, end_date, df)

    # Create two empty data.frame, collect samples according to who_name and date and percentage
    # Calculate total lineage frequency, in order to sort the lineage graph in a decreasing order.
    who = pd.DataFrame(
        columns=["Date"] + df["who_name"].value_counts().index.to_list() + ["nsamples"]
    )
    if select_range is True:
        who["Date"] = pd.date_range(start=start_date, end=end_date)
    else:
        who["Date"] = pd.date_range(
            start=min(df["sample_collection_date"]),
            end=max(df["sample_collection_date"]),
        )
    whoNum = who
    whoPer = who

    # Loop to fill empty pandas data.frames
    for i in range(windowSize - 1, whoNum.shape[0]):
        # Select date values
        dates = whoNum["Date"][range(i - (windowSize - 1), i)]
        # Selecting samples that are in that date range
        whoNumWindow = df[df["sample_collection_date"].isin(dates)]
        # Get count by who_name
        windowCount = whoNumWindow["who_name"].value_counts()
        # Record values if we have at least one sample in the date range
        if windowCount.shape[0] > 0:
            for j in range(0, windowCount.shape[0]):
                # Save value in correct column, getting column position looking by name
                whoNum.at[i, windowCount.index[j]] = windowCount[j]
                # Also record percentage
                whoPer.at[i, windowCount.index[j]] = round(
                    windowCount[j] / windowCount.sum() * 100, 2
                )
            # Record total samples used in that window
            # If we want position of name column whoNum.columns.get_loc("nsamples")
            whoNum.at[i, "nsamples"] = windowCount.sum()
            whoPer.at[i, "nsamples"] = windowCount.sum()

    # Get values by data and nsamples
    # whoPerMelted = pd.melt(whoPer, id_vars=["Date", "nsamples"]).dropna()

    # Fill NaN with 0 in order to avoid errors
    whoPer = whoPer.fillna(0)
    # We eliminated samples that were included on day 7 or 14, the first 6 or the first 13.
    whoPer = whoPer.iloc[windowSize - 1 :]

    # Select Lineages (which were ordered by frequency in decreasing order) for traces loop
    LINEAGES = whoPer.columns[range(1, whoPer.shape[1] - 1)].tolist()

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Scatter(
            x=whoPer["Date"],
            y=whoPer["nsamples"],
            mode="lines",
            line_color="#1C1B1B",
            line_width=2,
            name="Number of samples processed",
        ),
        secondary_y=True,
    )

    countLin = 0
    for LIN in LINEAGES:
        fig.add_trace(
            go.Bar(x=whoPer["Date"], y=whoPer[LIN], name=LIN, opacity=0.7),
            secondary_y=False,
        )
        countLin += 1

    # Set x-axis title
    fig.update_xaxes(
        title_text="<b>Date</b>",
        # rangebreaks=[dict(values=dt_breaks)]  # hide dates with no values
    )

    # Set y-axes titles
    fig.update_yaxes(
        range=[0, 100], title_text="<b>Lineage % relative", secondary_y=False
    )
    fig.update_yaxes(title_text="<b>Number of samples processed</b>", secondary_y=True)

    # Add figure title
    fig.update_layout(
        title_text="<b>RELECOV Spain - Lineage variation over time </b>("
        + str(windowSize)
        + " days)",
        barmode="stack",
        hovermode="x unified",
        legend_xanchor="center",  # use center of legend as anchor
        legend_orientation="h",  # show entries horizontally
        legend_x=0.5,  # put legend in center of x-axis
        bargap=0,  # gap between bars of adjacent location coordinates.
        bargroupgap=0,  # gap between bars of the same location coordinate.
        margin_l=100,
        margin_r=100,
        margin_b=50,
        margin_t=50,
    )

    return fig


if __name__ == "__main__":
    data = "/home/warlog/biohackathon/relecov-platform/relecov_dashboard/utils/graphics/fisabio_data.csv"
    plot = make_lineage_variaton_plot(
        data,
        start_date="2021-01-01",
        end_date="2022-03-13",
        select_range=True,  # False, need changes
        windowSize=14,
    )
    plot.write_html("lineage_variation_over_time.html")
