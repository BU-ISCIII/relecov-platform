# Local imports
import core.utils.plotly_graphics
import core.utils.rest_api
import core.utils.samples
import dashboard.utils.generic_process_data

def received_per_ccaa():
    """Fetch the data from LIMS and show them in a graphic bar"""
    samples_per_ccaa = (
            dashboard.utils.generic_graphic_data.get_graphic_json_data(
                "samples_received_per_ccaa"
            )
        )
    if samples_per_ccaa is None:
        # Execute the pre-processed task to get the data
        result = (
            dashboard.utils.generic_process_data.pre_proc_samples_received_per_ccaa()
        )
        if "ERROR" in result:
            return result
        samples_per_ccaa = (
            dashboard.utils.generic_graphic_data.get_graphic_json_data(
                "samples_received_per_ccaa"
            )
        )
    return core.utils.plotly_graphics.bar_graphic(
        data=samples_per_ccaa,
        col_names=["x", "y"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "", "height": 400},
    )


def received_per_lab():
    """Fetch the data from LIMS and show them in a graphic bar"""
    samples_per_lab = (
            dashboard.utils.generic_graphic_data.get_graphic_json_data(
                "samples_received_per_lab"
            )
        )
    if samples_per_lab is None:
        # Execute the pre-processed task to get the data
        result = (
            dashboard.utils.generic_process_data.pre_proc_samples_received_per_lab()
        )
        if "ERROR" in result:
            return result
        samples_per_lab = (
            dashboard.utils.generic_graphic_data.get_graphic_json_data(
                "samples_received_per_lab"
            )
        )
    return core.utils.plotly_graphics.bar_graphic(
        data=samples_per_lab,
        col_names=["x", "y"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={"title": "", "height": 400, "colors": "#1aff8c"},
    )


def received_samples_graph():
    """Fetch the number of samples received in the plaftorm and show them"""
    r_data = core.utils.samples.get_all_recieved_samples_with_dates(accumulated=True)
    data = {"x": [], "y": []}
    for r_dat in r_data:
        for key, value in r_dat.items():
            data["x"].append(key)
            data["y"].append(value)
    options = {
        "height": 450,
        "width": 400,
        "lines": "Samples",
        "x_axis": "Dates",
        "y_axis": "Number of samples",
        "x_title": "Date",
        "y_title": "Number of samples",
        "title": "",
        "xaxis": {"type": "date", "range": [min(data["x"]), max(data["x"])]},
    }
    return core.utils.plotly_graphics.line_graphic(data["x"], data["y"], options)
