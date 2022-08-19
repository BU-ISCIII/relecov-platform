import re
from relecov_core.models import Gene, OrganismAnnotation


def read_gff_file(a_file):
    """Read the gff file and return a dictionnary with gene names and positions"""
    f_data = {}
    with open(a_file, "r") as fh:
        lines = fh.readlines()
    # Read the gff heading notation
    f_data["gff_version"] = lines[0].strip()[-1]
    f_data["gff_spec_version"] = lines[1].strip().split(" ")[1]
    seq_reg = lines[5].strip().split(" ")
    f_data["sequence_region"] = seq_reg[-2] + "_" + seq_reg[-1]
    f_data["organism_code"] = seq_reg[1]
    f_data["genes"] = []
    for line in lines:
        if line.startswith("#"):
            continue
        l_split = line.split("\t")
        if l_split[2].lower() == "gene":
            gene_match = re.search(r".*;gene=(\w+);.*", line)
        if gene_match:
            g_info = {}
            g_info[""](gene_match.group(1))
            g_info.append(l_split[3])
            g_info.append(l_split[4])
            f_data["genes"].append(g_info)
    return f_data


def stored_gff(gff_parsed, user):
    """Save in database the gff information"""
    annotation_obj = OrganismAnnotation.objects.create_new_annotation(gff_parsed, user)
    for gene in gff_parsed["genes"]:
        gene["annotationID"] = annotation_obj
        gene["user"] = user
        Gene.objects.create_new_gene(gene)
