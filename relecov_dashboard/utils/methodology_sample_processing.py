import pandas as pd
from relecov_dashboard.utils.pre_processing_data import pre_proc_specimen_source_pcr_1
from relecov_core.utils.rest_api_handling import get_stats_data
from relecov_dashboard.utils.generic_functions import get_graphic_json_data
from relecov_dashboard.utils.plotly_graphics import bar_graphic, box_plot_graphic


def sample_processing_graphics():
    def get_pre_proc_data(graphic_name):
        """Get the pre-processed data for the graphic name.
        If there is not data stored for the graphic, it will query to store
        them before calling for the second time
        """
        json_data = get_graphic_json_data("specimen_source_pcr_1")
        if json_data is None:
            # Execute the pre-processed task to get the data
            result = pre_proc_specimen_source_pcr_1()
            if "ERROR" in result:
                return result
        json_data = get_graphic_json_data("specimen_source_pcr_1")
        # Convert string to float values
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
        options={"title": "Nucleic acid extraction protocol", "height": 400},
    )
    cts_specimen_data = get_pre_proc_data("specimen_source_pcr_1")

    sample_processing["cts_specimen"] = box_plot_graphic(
        cts_specimen_data,
        {"title": "Boxplot Cts / specimen source", "height": 400, "width": 520},
    )

    return sample_processing
