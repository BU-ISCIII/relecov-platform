# Generic imports

# Local imports
import core.utils.plotly_graphics


def perc_gauge_graphic(values):
    data = {}
    try:
        analized = values.get("analized", 0)
        received = values.get("received", 0)
        if received == 0:
            data["value"] = 0.0
        else:
            x = analized / received * 100
            data["value"] = round(x, 2)
    except Exception as e:
        return {"ERROR": f"Failed to generate gauge graphic: {str(e)}"}

    gauge_graph = core.utils.plotly_graphics.gauge_graphic(data)
    return gauge_graph