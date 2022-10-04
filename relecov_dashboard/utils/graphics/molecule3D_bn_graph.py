import os
from django_plotly_dash import DjangoDash
import dash_table
from dash.dependencies import Input, Output
import pandas as pd
import dash_bio as dashbio
import dash_html_components as html
from relecov_platform import settings

# PDB parserThis module contains a class that can read PDB files and return a dictionary of structural data
import parmed as pmd


class PdbParser:
    """
    Parse the protein data bank (PDB) file to generate
    input data for Molecule3dViewer, Molecule2dViewer and Speck components.
    @param pdb_path
    Path to PDB file (either HTTP or local path).
    """

    def __init__(self, s: str):
        """
        if re.search(r"^[1-9][0-9A-z]{3}$", s):
            # d is PDB id (https://proteopedia.org/wiki/index.php/PDB_code)
            self.structure = pmd.download_PDB(s)
        else:
            # d is HTTP url or local file
            self.structure = pmd.load_file(s)
        """
        self.structure = pmd.load_file(s)
        self.atoms = self.structure.atoms
        self.bonds = self.structure.bonds

    def mol3d_data(self):  # -> dict
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


def create_mol3d_style(atoms):
    atom_styles = []
    for a in atoms:
        atom_styles.append({"visualization_type": "cartoon", "color": "#ced4da"})
    return atom_styles


def get_spike_mutations(csv_file):
    df = pd.read_csv(csv_file, sep=",")
    spike_df = df.loc[df["GENE"] == "S"]
    return spike_df


def get_table_selection(df):
    table_selection = df[["POS", "REF", "ALT", "HGVS_C", "HGVS_P", "HGVS_P_1LETTER"]]
    table_selection = table_selection.drop_duplicates()
    table_selection = table_selection.sort_values(by=["POS"])
    return table_selection


def create_model3D_bn():

    app = DjangoDash("model3D_bn")

    pdb_file = PdbParser(
        os.path.join(
            settings.BASE_DIR, "relecov_dashboard", "utils", "pdb_files", "7dwz.pdb"
        )
    )

    data = pdb_file.mol3d_data()
    styles = create_mol3d_style(data["atoms"])

    df = pd.DataFrame(data["atoms"])

    df["positions"] = df["positions"].apply(lambda x: ", ".join(map(str, x)))

    app.layout = html.Div(
        [
            dash_table.DataTable(
                id="selecting-specific-spike-residue-table",
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict("records"),
                row_selectable="single",
                page_size=10,
            ),
            dashbio.Molecule3dViewer(
                id="zooming-specific-molecule3d-zoomto",
                modelData=data,
                styles=styles,
                selectionType="residue",
            ),
        ]
    )

    @app.callback(
        Output("zooming-specific-molecule3d-zoomto", "zoomTo"),
        Output("zooming-specific-molecule3d-zoomto", "labels"),
        Output("zooming-specific-molecule3d-zoomto", "styles"),
        Input("selecting-specific-spike-residue-table", "selected_rows"),
        prevent_initial_call=True,
    )
    def residue(selected_row):
        row = df.iloc[selected_row]
        row["positions"] = row["positions"].apply(
            lambda x: [float(x) for x in x.split(",")]
        )
        atoms = df[df["residue_position"] == row["residue_position"].iloc[0]]
        list_atoms = atoms["serial"].tolist()
        new_atom_styles = []
        for a in range(len(styles)):
            if a in list_atoms:
                new_atom_styles.append(
                    {"visualization_type": "cartoon", "color": "#ff7d00"}
                )
            else:
                new_atom_styles.append(
                    {"visualization_type": "cartoon", "color": "#ced4da"}
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
            new_atom_styles,
        ]
