from django.shortcuts import render
from relecov_dashboard.utils.graphics.lineages_in_time_graph import (
    create_lineage_in_time_graph,
)
from relecov_dashboard.utils.graphics.molecule3D_graph import create_molecule3D_graph
from relecov_dashboard.utils.graphics.needle_plot_graph import create_needle_plot_graph


def dashboard(request):
    return render(request, "relecov_dashboard/dashboard.html")


def lineages_in_time(request):
    create_lineage_in_time_graph()
    return render(request, "relecov_dashboard/lineages_in_time.html")


def methodology_index(request):
    return render(request, "relecov_dashboard/methodology.html")


def needle_plot(request):
    create_needle_plot_graph()
    return render(request, "relecov_dashboard/needle_plot.html")


def molecular_3D(request):
    create_molecule3D_graph()
    return render(request, "relecov_dashboard/molecular_3D.html")


def hackaton_group1(request):
    return render(request, "relecov_dashboard/hackaton_group1.html")


def hackaton_group2(request):
    return render(request, "relecov_dashboard/hackaton_group2.html")


def hackaton_group3(request):
    return render(request, "relecov_dashboard/hackaton_group3.html")


def hackaton_group4(request):
    return render(request, "relecov_dashboard/hackaton_group4.html")
