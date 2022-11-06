from relecov_dashboard.utils.graphics.plotly_dashboard_graphics import create_line_plot


from relecov_core.utils.handling_samples import get_all_recieved_samples_with_dates


def display_received_samples_graph():
    """Fetch the number of samples received in the plaftorm and show them"""
    r_data = get_all_recieved_samples_with_dates(accumulated=True)
    data = {"x": [], "y": []}
    for r_dat in r_data:
        for key, value in r_dat.items():
            data["x"].append(key)
            data["y"].append(value)
    options = {
        "height": 450,
        "width": 500,
        "lines": "Samples",
        "x_axis": "Dates",
        "y_axis": "Number of samples",
    }
    return create_line_plot(data, options)
