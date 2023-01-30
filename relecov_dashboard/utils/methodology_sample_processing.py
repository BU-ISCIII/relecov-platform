import pandas as pd
from relecov_dashboard.utils.pre_processing_data import (
    pre_proc_specimen_source_pcr_1,
    pre_proc_extraction_protocol_pcr_1,
    pre_proc_calculation_date,
)
from relecov_core.utils.rest_api_handling import get_stats_data
from relecov_dashboard.utils.generic_functions import get_graphic_json_data
from relecov_dashboard.utils.graphics.plotly_graphics import bar_graphic, box_plot_graphic


def sample_processing_graphics():
    def get_pre_proc_data(graphic_name):
        """Get the pre-processed data for the graphic name.
        If there is not data stored for the graphic, it will query to store
        them before calling for the second time
        """

        # map_graphic = {"extraction_protocol_pcr_1" : pre_proc_specimen_source_pcr_1(), "specimen_source_pcr_1": pre_proc_extraction_protocol_pcr_1(), "calculation_date": pre_proc_calculation_date()}

        json_data = get_graphic_json_data(graphic_name)
        if json_data is None:
            # Execute the pre-processed task to get the data
            if graphic_name == "extraction_protocol_pcr_1":
                result = pre_proc_specimen_source_pcr_1()
            elif graphic_name == "specimen_source_pcr_1":
                result = pre_proc_extraction_protocol_pcr_1()
            elif graphic_name == "calculation_date":
                result = pre_proc_calculation_date()
            else:
                return {"ERROR": "pre-processing not defined"}
            if "ERROR" in result:
                return result
            json_data = get_graphic_json_data(graphic_name)
        # Convert string to float values
        if graphic_name == "calculation_date":
            return [json_data]
        data = []

        for key, values in json_data.items():
            tmp_data = []
            for str_val, numbers in values.items():
                try:
                    float_val = float(str_val)
                except ValueError:
                    continue
                tmp_data += [float_val] * numbers
            data.append({key: tmp_data})
        return data

    def fetching_data_for_sample_processing(project_field, columns):

        # get stats utilization fields from LIMS about nucleic acid extaction
        # protocol
        lims_data = get_stats_data(
            {
                "sample_project_name": "Relecov",
                "project_field": project_field,
            }
        )
        if "ERROR" in lims_data:
            return lims_data
        if "," in project_field:
            data = []
            for key, values in lims_data.items():
                tmp_data = []
                for str_val, numbers in values.items():
                    try:
                        float_val = float(str_val)
                    except ValueError:
                        continue
                    tmp_data += [float_val] * numbers
                data.append({key: tmp_data})
            return data

        else:
            return pd.DataFrame(lims_data.items(), columns=columns)

    sample_processing = {}

    # extraction protocol graphics
    extraction_protocol_df = fetching_data_for_sample_processing(
        project_field="nucleic_acid_extraction_protocol", columns=["protocol", "number"]
    )
    if "ERROR" in extraction_protocol_df:
        return extraction_protocol_df
    sample_processing["nucleic_protocol"] = bar_graphic(
        data=extraction_protocol_df,
        col_names=["protocol", "number"],
        legend=[""],
        yaxis={"title": "Number of samples"},
        options={
            "title": "Nucleic acid extraction protocol",
            "height": 400,
            "width": 320,
        },
    )

    cts_extraction_data = get_pre_proc_data("extraction_protocol_pcr_1")

    sample_processing["cts_extraction"] = box_plot_graphic(
        cts_extraction_data,
        {"title": "Boxplot Cts / Extraction protocol", "height": 400, "width": 520},
    )
    # expecimen source graphics
    cts_specimen_data = get_pre_proc_data("specimen_source_pcr_1")

    sample_processing["cts_specimen"] = box_plot_graphic(
        cts_specimen_data,
        {"title": "Boxplot Cts / specimen source", "height": 400, "width": 600},
    )
    # calculate the number of days spent in each state before moved on to next step
    calculation_date_data = get_pre_proc_data("calculation_date")
    sample_processing["calculation_date"] = box_plot_graphic(
        calculation_date_data,
        {"title": "Time between sample step actions", "height": 400, "width": 420},
    )
    return sample_processing
