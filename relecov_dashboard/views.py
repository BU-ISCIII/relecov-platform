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

#from dash import Input, Output#Dash, dcc, html, 
from dash.dependencies import Input, Output

# IMPORT FROM UTILS
from relecov_core.utils.random_data import *
from relecov_core.utils.parse_files import *


def index(request):
    #df_table = pd.read_csv("relecov_core/docs/cogUK/table_3_2022-04-12.csv")
    sequences_list = generate_random_sequences()
    #weeks_list = generate_weeks()
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
    print(len(df["Week"]))
    print(df["Week"].min())
    print(df["Week"].max())
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
                id="graph-with-slider",
                figure=fig
                
            ),
            html.Br(),
            dcc.Slider(
                min = df["Week"].min(),
                max = df["Week"].max(),
                step=None,
                value=df["Week"].min(),
                marks={str(week): str(week) for week in df['Week'].unique()},
                id='week-slider'
            ),
            html.Div(
                style={"background": "white"},
                children=[
                    html.H1(
                        children="Prueba de tabla",
                        style={"color": "#7FDBFF"}
                    ),
                    html.Div(
                        style={"border":"1px solid"},    
                        #children=generate_table(df_table)
                    )
                ]    
            )
       ]
    )
    @app.callback(
    Output('graph-with-slider', 'figure'),
    Input('week-slider', 'value'))
    
    def update_figure(selected_week):
        sequences_list2 = []
        lineage_week_list2 =[]
        lineage_list2 = []

        for variant in variant_data:
            
            if(int(variant["lineage_dict"]["week"]) >= int(selected_week)):
                lineage_list2.append(variant["lineage_dict"]["lineage"])
                lineage_week_list2.append(variant["lineage_dict"]["week"])
                
        sequences_list2 = sequences_list[len(lineage_list)-len(lineage_list2):]
        
        df = pd.DataFrame(
            {
                "Week": lineage_week_list2,
                "Sequences": sequences_list2,
                "Variant": lineage_list2,
            }
        )
             
        fig = px.bar(df, x="Week", y="Sequences", color="Variant", barmode="stack",
                        hover_name="Variant")

        fig.update_layout(transition_duration=500)
        return fig
        
    return render(request, "relecov_dashboard/index.html")


def index2(request):
    return render(request, "relecov_dashboard/index2.html")



"""
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
"""

