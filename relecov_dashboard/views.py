from django.shortcuts import render
from relecov_dashboard.utils.graphics.lineages_in_time_graph import (
    create_lineage_in_time_graph,
)
from relecov_dashboard.utils.graphics.molecule3D_graph import (
    create_molecule3D_graph,
    create_molecule3D_zoom_specific_residues,
)
from relecov_dashboard.utils.graphics.needle_plot_graph import create_needle_plot_graph


def variant_dashboard(request):
    # create_lineage_in_time_graph()
    # print(request.method)
    return render(request, "relecov_dashboard/variant_dashboard.html")


def methodology_dashboard(request):
    return render(request, "relecov_dashboard/methodology_dashboard.html")


def lineages_voc(request):
    create_lineage_in_time_graph()
    create_needle_plot_graph(sample=None)
    create_molecule3D_graph()
    create_molecule3D_zoom_specific_residues()
    return render(request, "relecov_dashboard/dashboard_templates/lineages_voc.html")


"""
def main_dashboard(request):
    return render(request, "relecov_dashboard/dashboard.html")


def needle_plot(request):
    # create_needle_plot_graph(sample=None)
    return render(request, "relecov_dashboard/needle_plot.html")


def molecular_3D_bootstrap(request):
    create_molecule3D_graph()
    return render(request, "relecov_dashboard/molecular_3D.html")
"""
