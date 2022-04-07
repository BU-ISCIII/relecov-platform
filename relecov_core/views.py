from distutils.log import debug
from multiprocessing import context
from relecov_core.models import *
from django.shortcuts import render
from relecov_core.utils.feed_db import clear_all_tables
from relecov_core.utils.random_data import generate_random_sequences, generate_weeks
#IMPORT FROM UTILS
from relecov_core.utils import *
#plotly dash
import dash_core_components as dcc
import dash_html_components as html
from django_plotly_dash import DjangoDash
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd


def index(request):
    context = {}
    return render(request, "relecov_core/index.html", context)
def variants(request):
    context = {}
    return render(request, "relecov_core/variants.html", context)

def documentation(request):
    context = {}
    return render(request, "relecov_core/documentation.html", context)

def readTest(request):
    #fields => SAMPLE(0), CHROM(1), POS(2), REF(3), ALT(4), FILTER(5), DP(6),  REF_DP(7), ALT_DP(8), AF(9), GENE(10), EFFECT(11), HGVS_C(12), 
    #   HGVS_P(13), HGVS_P1LETTER(14), CALLER(15), LINEAGE(16)
    context = {}
    #clear_all_tables()
    data_array = []#one field per position
    lineage_dict = {}
    lineage_list = []
    
    #fields => SAMPLE(0), CHROM(1), POS(2), REF(3), ALT(4), FILTER(5), DP(6),  REF_DP(7), ALT_DP(8), AF(9), GENE(10), EFFECT(11), HGVS_C(12), 
    #   HGVS_P(13), HGVS_P1LETTER(14), CALLER(15), LINEAGE(16)
    with open("relecov_core/docs/variantLuisTableCSV.csv") as fh:
        lines = fh.readlines()
    for line in lines[1:]:
        data_array = line.split(",")
        #lineage
        #lineage_dict["lineage"] = data_array[16]
        #lineage_dict["week"] = data_array[17]
        #lineage_dict_copy = lineage_dict.copy()
        #lineage_list.append(lineage_dict_copy)
        #print(lineage_list)
        
    week=["1", "2", "3", "4", "5", "6", "7", "8",]
    fig = go.Figure(go.Bar(x=week, y=[2,5,9,12,16,9,4,2], name="B.1.177"))
    fig.add_trace(go.Bar(x=week, y=[1, 4, 9, 16, 8,5,2,1], name="BA.1.1"))
    fig.add_trace(go.Bar(x=week, y=[0, 0, 1, 2, 6, 9, 7, 4], name="BA.1"))
    fig.add_trace(go.Bar(x=week, y=[0, 0, 0, 3, 7, 9, 10, 5], name="AY.43"))
    fig.add_trace(go.Bar(x=week, y=[0, 0, 0, 2, 5, 8, 9, 4], name="AY.44"))
    fig.add_trace(go.Bar(x=week, y=[0, 0, 0, 1, 4, 9, 5, 1], name="AY.4"))
    fig.add_trace(go.Bar(x=week, y=[0, 0, 0, 0, 3, 6, 4, 2], name="AY.124"))
    fig.add_trace(go.Bar(x=week, y=[0, 0, 0, 0, 1, 4, 16, 10], name="AY.113"))
    fig.add_trace(go.Bar(x=week, y=[0, 0, 0, 0, 0, 4, 11, 16], name="AY.102.2"))
    
    fig.update_layout(barmode="stack")
    #fig.update_xaxes(showgrid = True,ticks = "outside")#, categoryorder="array", categoryarray= ["1", "2", "3", "4", "5", "6", "7", "8",]
    fig.show()
    """
    #Context    
    context = {
        "variant":variant_list, 
        "chromosome":chromosome_list,
        "effect":effect_list,
        "sample":sample_list,
        "filter":filter_list,
        "caller":caller_list,
        "lineage":lineage_list,
        "gene":gene_list,
        }      
    """
    return render(request, "relecov_core/documentation.html", context)  

#plotly dash example 1
def plotly_ex(request):
    app = DjangoDash("SimpleExample")   # replaces dash.Dash
    
    colors = {
    "background": "#111111",
    "text": "#7FDBFF"
    }

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
    df = pd.DataFrame({
        "Week": ["1", "2", "3", "4", "5", "6", "7", "8",],
        "Sequences": [1, 4, 9, 16, 8,5,2,1],
        "Variant": ["B.1.177", "BA.1.1", "BA.1", "AY.43", "AY.44", "AY.4", "AY.124", "AY.113"]
        
    })

    fig = px.bar(df, x="Week", y="Sequences", color="Variant", barmode="group")

    fig.update_layout(
        plot_bgcolor=colors["background"],
        paper_bgcolor=colors["background"],
        font_color=colors["text"]
    )

    app.layout = html.Div(style={"backgroundColor": colors["background"]}, children=[
        html.H1(
            children="Hello Dash",
            style={
                "textAlign": "center",
                "color": colors["text"]
            }
        ),

        html.Div(children="Dash: A web application framework for your data.", style={
            "textAlign": "center",
            "color": colors["text"]
        }),

        dcc.Graph(
            id="example-graph-2",
            figure=fig
        )
    ])

    return render(request, "relecov_core/documentation.html", {})

#plotly dash example 2
def plotly_ex2(request):
    data_array = []
    lineage_list = []
    #import random
    sequences_list = generate_random_sequences()
    weeks_list = generate_weeks()

    with open("relecov_core/docs/variants1.csv") as fh:
        lines = fh.readlines()

    for line in lines[1:]:
        data_array = line.split(",")
        # lineage
        lineage_list.append(data_array[16])
    
    
    app = DjangoDash("SimpleExample2")   # replaces dash.Dash
    
    colors = {
    "background": "#111111",
    "text": "#7FDBFF"
    }
    # assume you have a "long-form" data frame, see https://plotly.com/python/px-arguments/ for more options
    df = pd.DataFrame({
        "Week": weeks_list,
        "Sequences": sequences_list,
        "Variant": lineage_list
        
    })

    fig = px.bar(df, x="Week", y="Sequences", color="Variant", barmode="stack")

    fig.update_layout(
        plot_bgcolor=colors["background"],
        paper_bgcolor=colors["background"],
        font_color=colors["text"]
    )

    app.layout = html.Div(style={"backgroundColor": colors["background"]}, children=[
        html.H1(
            children="Hello Dash",
            style={
                "textAlign": "center",
                "color": colors["text"]
            }
        ),

        html.Div(children="Dash: A web application framework for your data.", style={
            "textAlign": "center",
            "color": colors["text"]
        }),

        dcc.Graph(
            id="example-graph-2",
            figure=fig
        )
    ])

    return render(request, "relecov_core/documentation.html", {})

