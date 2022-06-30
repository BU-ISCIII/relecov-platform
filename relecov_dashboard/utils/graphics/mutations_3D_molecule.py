import dash
from dash.dependencies import Input, Output
from dash import dash_table
import dash_bio as dashbio
from dash_bio.utils import PdbParser, create_mol3d_style
from dash import html
import pandas as pd

"""PDB parser
This module contains a class that can read PDB files and return a dictionary of structural data"""
import re
import parmed as pmd


class PdbParser:
    """
    Parse the protein data bank (PDB) file to generate
    input data for Molecule3dViewer, Molecule2dViewer and Speck components.
    @param pdb_path
    Path to PDB file (either HTTP or local path).
    """

    def __init__(self, s: str):

        if re.search(r"^[1-9][0-9A-z]{3}$", s):
            # d is PDB id (https://proteopedia.org/wiki/index.php/PDB_code)
            self.structure = pmd.download_PDB(s)
        else:
            # d is HTTP url or local file
            self.structure = pmd.load_file(s)

        self.atoms = self.structure.atoms
        self.bonds = self.structure.bonds

    def mol3d_data(self) -> dict:
        """
        Generate input data for Molecule3dViewer component.
        """

        data = {"atoms": [], "bonds": []}

        for a in self.atoms:
            data["atoms"].append(
                {
                    "serial": a.idx,
                    "name": a.name,
                    "elem": a.element_name,
                    "positions": [a.xx, a.xy, a.xz],
                    "mass_magnitude": a.mass,
                    "residue_index": a.residue.idx,
                    "residue_name": a.residue.name,
                    "chain": a.residue.chain,
                    "residue_position": a.residue.number,
                }
            )

        for b in self.bonds:
            data["bonds"].append(
                {
                    "atom1_index": b.atom1.idx,
                    "atom2_index": b.atom2.idx,
                    "bond_order": b.order,
                }
            )

        return data


def get_spike_mutations(csv_file):
    df = pd.read_csv(csv_file, sep=",")
    spike_df = df.loc[df["GENE"] == "S"]
    return spike_df


def get_table_selection(df):
    table_selection = df[["POS", "REF", "ALT", "HGVS_C", "HGVS_P", "HGVS_P_1LETTER"]]
    table_selection = table_selection.drop_duplicates()
    table_selection = table_selection.sort_values(by=["POS"])
    return table_selection


file_csv = "/home/vhir/Documents/biohackathon_relecov/Hackaton/variants_long_table.csv"

spike_mutations = get_table_selection(get_spike_mutations(file_csv))


app = dash.Dash("model3D")

parser = PdbParser("/home/vhir/Documents/biohackathon_relecov/Hackaton/7dwz.pdb")
# structure = pmd.load_file("/home/vhir/Documents/biohackathon_relecov/Hackaton/7dwz.pdb")
# import pdb; pdb.set_trace()
data = parser.mol3d_data()
styles = create_mol3d_style(data["atoms"], visualization_type="cartoon")


df = pd.DataFrame(data["atoms"])


df["positions"] = df["positions"].apply(lambda x: ", ".join(map(str, x)))

app.layout = html.Div(
    [
        dash_table.DataTable(
            id="zooming-specific-residue-table",
            columns=[{"name": i, "id": i} for i in spike_mutations.columns],
            data=spike_mutations.to_dict("records"),
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
    row = spike_mutations.iloc[selected_row]
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
