import pandas as pd
import plotly.express as px
import numpy as np


df = px.data.tips()
# create the bins
counts, bins = np.histogram(df.total_bill, bins=range(0, 60, 5))
bins = 0.5 * (bins[:-1] + bins[1:])

fig = px.bar(x=bins, y=counts, labels={"x": "total_bill", "y": "count"})
fig.show()

def select_range_date(start_date,end_date,df):
    """"
    Select range date
    """
    # Select DataFrame rows between two dates
    mask = (df['sample_collection_date'] > start_date) & (df['sample_collection_date'] <= end_date)
    df2 = df.loc[mask]
    return df

if __name__ == "__main__":
    # Load data
    fis = '/home/warlog/biohackathon/relecov-platform/relecov_dashboard/utils/graphics/fisabio_data.csv'
    df = pd.read_csv(fis)
    # Select range or no
    start_date = '2021-01-01'
    end_date = '2021-12-31'
    fissel = select_range_date(start_date, end_date, df)


    # Color plot (better use scale, with more colors)
    my_colors = [  ## add the standard plotly colors
        '#bab7bd',  # //
        '#be78fe',  # //
        '#ff3333',  # // brick red
        '#2ca02c',  # // cooked asparagus green
        '#ffdc1c',  # // safety orange
        '#2d8bcc'  # // muted blue
    ]



# import json
#
# # Opening JSON file
# def parse_json_file(json_file):
#     """
#     This function loads a json file and returns a python dictionary.
#     """
#     json_parsed = {}
#     # f = open(json_file)
#     with open(json_file) as f:
#         json_parsed["data"] = json.load(f)
#     return json_parsed
#
# # De este JSON nos interesa sequencing_sample_id + sample_collection_date
# data1 = parse_json_file('/home/warlog/biohackathon/relecov-platform/relecov_dashboard/utils/graphics/data_json_lineage/bioinfo_metadata.json')
# # De este JSON nos interesa ID + lineage_name
# data2 = parse_json_file('/home/warlog/biohackathon/relecov-platform/relecov_dashboard/utils/graphics/data_json_lineage/processed_metadata_lab_20220208_20220613.json')

