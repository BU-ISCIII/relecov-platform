from relecov_dashboard.utils.plotly_graphics import box_plot_graphic
from relecov_core.models import BioinfoAnalysisValue


def bioinfo_graphics():
    def get_percentage_data():
        per_data = []
        graph_list = ["per_Ns", "per_reads_host", "per_reads_virus", "per_unmapped"]
        for graph in graph_list:
            if BioinfoAnalysisValue.objects.filter(
                bioinfo_analysis_fieldID__property_name__exact=graph
            ).exists():
                str_data = list(
                    BioinfoAnalysisValue.objects.filter(
                        bioinfo_analysis_fieldID__property_name__exact=graph
                    ).values_list("value", flat=True)
                )
                try:
                    per_data.append({graph: list(map(float, str_data))})
                except ValueError:
                    filter_list = []
                    for value in str_data:
                        try:

                            filter_list.append(float(value))
                        except ValueError:
                            continue
                    per_data.append({graph: filter_list})

        return per_data

    bioinfo = {}
    percentage_data = get_percentage_data()
    bioinfo["boxplot_comparation"] = box_plot_graphic(
        percentage_data,
        {"title": "Boxplot Percentage", "height": 400, "width": 420},
    )
    return bioinfo
