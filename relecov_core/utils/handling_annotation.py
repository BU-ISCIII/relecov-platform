import re

from relecov_core.models import Gene, OrganismAnnotation


def get_annotations():
    """Get the information of the existing loaded annotations and return a
    list with all
    """
    ann_list = []
    if OrganismAnnotation.objects.all().exists():
        annotation_objs = OrganismAnnotation.objects.all().order_by("organism_code")
        for annotation_obj in annotation_objs:
            ann_list.append(annotation_obj.get_full_information())
    return ann_list


def read_gff_file(a_file):
    """Read the gff file and return a dictionnary with gene names and positions"""
    # read the uploaInMemory file and convert in a list of line
    b_lines = b""
    for chunk in a_file.chunks():
        b_lines += chunk
    lines = b_lines.decode("utf-8").split("\n")

    f_data = {}
    # Read the gff heading notation
    f_data["gff_version"] = lines[0].strip()[-1]
    f_data["gff_spec_version"] = lines[1].strip().split(" ")[1]
    seq_reg = lines[5].strip().split(" ")
    f_data["sequence_region"] = seq_reg[-2] + "_" + seq_reg[-1]
    f_data["organism_code"] = seq_reg[1]
    f_data["genes"] = []
    for line in lines:
        if line.startswith("#") or line == "":
            continue
        l_split = line.split("\t")
        if l_split[2].lower() == "gene":
            gene_match = re.search(r".*;gene=(\w+);.*", line)
            if gene_match:
                g_info = {}
                g_info["gene_name"] = gene_match.group(1)
                g_info["gene_start"] = l_split[3]
                g_info["gene_end"] = l_split[4]
                f_data["genes"].append(g_info)
    return f_data


def stored_gff(gff_parsed, user):
    """Save in database the gff information"""
    gff_parsed["user"] = user
    annotation_obj = OrganismAnnotation.objects.create_new_annotation(gff_parsed)
    for gene in gff_parsed["genes"]:
        gene["annotationID"] = annotation_obj
        gene["user"] = user
        gene["gff_anotationID"] = annotation_obj
        Gene.objects.create_new_gene(gene)
    return
