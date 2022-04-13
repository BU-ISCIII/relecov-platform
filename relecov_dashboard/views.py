from django.shortcuts import render
from plotly.offline import plot
import plotly.graph_objects as go

# plotly dash
import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash

# import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# IMPORT FROM UTILS
from relecov_core.utils.random_data import *
from relecov_core.utils.parse_files import *


def index(request):
    df_table = pd.read_csv("relecov_core/docs/cogUK/table_3_2022-04-12.csv")
    sequences_list = generate_random_sequences()
    weeks_list = generate_weeks()
    lineage_list = []
    lineage_week_list = []
    variant_data = parse_csv_into_list_of_dicts(
        "relecov_core/docs/variantLuisTableCSV.csv"
    )
    for variant in variant_data:
        lineage_list.append(variant["lineage_dict"]["lineage"])
        lineage_week_list.append(variant["lineage_dict"]["week"])

    app = DjangoDash("SimpleExample")  # replaces dash.Dash

    colors = {"background": "#111111", "text": "#7FDBFF"}
    # assume you have a "long-form" data frame, see https://plotly.com/python/px-arguments/ for more options
    df = pd.DataFrame(
        {
            "Week": lineage_week_list,
            "Sequences": sequences_list,
            "Variant": lineage_list,
        }
    )

    fig = px.bar(df, x="Week", y="Sequences", color="Variant", barmode="stack")

    fig.update_layout(
        plot_bgcolor=colors["background"],
        paper_bgcolor=colors["background"],
        font_color=colors["text"],
    )

    app.layout = html.Div(
        style={"backgroundColor": colors["background"]},
        children=[
            html.H1(
                children="Variant Dashboard",
                style={"textAlign": "center", "color": colors["text"]},
            ),
            html.Div(
                children="Variant data.",
                style={"textAlign": "center", "color": colors["text"]},
                
    
            ),
            dcc.Graph(
                # id="example-graph-2",
                figure=fig
                
            ),
            
        ],
    )
    
    

    return render(request, "relecov_dashboard/index.html")


def index2(request):
    df = pd.read_csv("relecov_core/docs/cogUK/table_3_2022-04-12.csv")
    
    


    app = DjangoDash("SimpleExampleTable")

    app.layout = html.Div([
        html.H4(children='Variant Table'),
        generate_table(df)
    ])

    return render(request, "relecov_dashboard/index2.html")


def index3(request):
    def scatter():
        x1 = [1, 2, 3, 4]
        y1 = [30, 35, 25, 45]

        trace = go.Scatter(x=x1, y=y1)
        layout = dict(
            title="Simple Graph",
            xaxis=dict(range=[min(x1), max(x1)]),
            yaxis=dict(range=[min(y1), max(y1)]),
        )

        fig = go.Figure(data=[trace], layout=layout)
        plot_div = plot(fig, output_type="div", include_plotlyjs=False)
        return plot_div

    context = {"plot1": scatter()}

    return render(request, "relecov_dashboard/index3.html", context)

def generate_table(dataframe, max_rows=14):
        return html.Table([
        html.Thead(
            html.Tr(
                [html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])