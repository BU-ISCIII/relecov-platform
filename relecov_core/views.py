from distutils.log import debug
from multiprocessing import context, Manager
from relecov_core.models import *
from django.shortcuts import render
from relecov_core.utils.feed_db import *
from relecov_core.utils.random_data import generate_random_sequences, generate_weeks
from relecov_core.utils.parse_files import *

# IMPORT FROM UTILS
from relecov_core.utils import *

# plotly dash
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


# plotly dash example
def plotly_ex(request):
    #sequences_list = generate_random_sequences()
    #weeks_list = generate_weeks()

    variant_data = parse_csv_into_list_of_dicts("relecov_core/docs/variantLuisTableCSV.csv")
    print(type(variant_data))
    print(type(variant_data[0]))
        
        
    
    #for i in range(len(var)):
    #    insert_into_variant_table(var[i]["variant_dict"])
        
        
        
        #print(var[i]["variant_dict"])
    
    
    
    
    """
        app = DjangoDash("SimpleExample2")  # replaces dash.Dash

        colors = {"background": "#111111", "text": "#7FDBFF"}
        # assume you have a "long-form" data frame, see https://plotly.com/python/px-arguments/ for more options
        df = pd.DataFrame(
            {"Week": weeks_list, "Sequences": sequences_list, "Variant": lineage_list}
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
                    children="Hello Dash",
                    style={"textAlign": "center", "color": colors["text"]},
                ),
                html.Div(
                    children="Dash: A web application framework for your data.",
                    style={"textAlign": "center", "color": colors["text"]},
                ),
                dcc.Graph(
                    # id="example-graph-2",
                    figure=fig
                ),
            ],
        )
    """
    return render(request, "relecov_core/documentation.html", {})

