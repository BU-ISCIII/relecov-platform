import os
from django_plotly_dash import DjangoDash
import dash_table
from dash.dependencies import Input, Output
import pandas as pd
import dash_bio as dashbio
import dash_html_components as html
from dash_bio.utils import PdbParser, create_mol3d_style
from relecov_platform import settings

"""
import dash
from dash.dependencies import Input, Output
from dash import dash_table
import dash_bio as dashbio
from dash_bio.utils import PdbParser, create_mol3d_style
from dash import html
import pandas as pd
"""
app = DjangoDash("model3D")

# parser = PdbParser("/home/vhir/Documents/biohackathon_relecov/Hackaton/7bnm.cif")
parser = PdbParser(
    os.path.join(
        settings.BASE_DIR, "relecov_dashboard", "utils", "pdb_files", "7dwz.pdb"
    )
)
data = parser.mol3d_data()
styles = create_mol3d_style(data["atoms"], visualization_type="cartoon")

df = pd.DataFrame(data["atoms"])

df["positions"] = df["positions"].apply(lambda x: ", ".join(map(str, x)))

app.layout = html.Div(
    [
        dash_table.DataTable(
            id="zooming-specific-residue-table",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
            row_selectable="single",
            page_size=10,
        ),
        dashbio.Molecule3dViewer(
            id="zooming-specific-molecule3d-zoomto", modelData=data, styles=styles
        ),
    ]
)


@app.callback(
    Output("zooming-specific-molecule3d-zoomto", "zoomTo"),
    Output("zooming-specific-molecule3d-zoomto", "labels"),
    Input("zooming-specific-residue-table", "selected_rows"),
    prevent_initial_call=True,
)
def residue(selected_row):
    row = df.iloc[selected_row]
    row["positions"] = row["positions"].apply(
        lambda x: [float(x) for x in x.split(",")]
    )
    return [
        {
            "sel": {"chain": row["chain"], "resi": row["residue_index"]},
            "animationDuration": 1500,
            "fixedPath": True,
        },
        [
            {
                "text": "Residue Name: {}".format(row["residue_name"].values[0]),
                "position": {
                    "x": row["positions"].values[0][0],
                    "y": row["positions"].values[0][1],
                    "z": row["positions"].values[0][2],
                },
            }
        ],
    ]
