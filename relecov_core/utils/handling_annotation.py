import re

from relecov_core.models import Gene, OrganismAnnotation, Chromosome

from relecov_core.core_config import (
    ERROR_ANNOTATION_ORGANISM_ALREADY_EXISTS,
    HEADING_FOR_ANNOTATION_GENE,
)


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


def check_if_annotation_exists(annot_id):
    """check if the annotation id exists on database"""
    if OrganismAnnotation.objects.filter(pk__exact=annot_id).exists():
        return True
    return False


def check_if_organism_version_exists(organism, version):
    """Check if the organism and version is already in database"""
    if OrganismAnnotation.objects.filter(
        organism_code__iexact=organism, organism_code_version__iexact=version
    ).exists():
        return True
    return False


def get_annotation_data(annot_id):
    """Get tha annotation genes defined for the annotation id"""
    annot_data = {}
    annot_obj = get_annotation_obj_from_id(annot_id)
    chromosome_obj = annot_obj.get_chromosome_obj()
    annot_data["organism"] = annot_obj.get_organism_code()
    annot_data["version"] = annot_obj.get_organism_code_version()

    if Gene.objects.filter(chromosomeID=chromosome_obj).exists():
        gene_objs = Gene.objects.filter(chromosomeID=chromosome_obj).order_by(
            "gene_start"
        )
        genes = []
        for gene_obj in gene_objs:
            g_info = gene_obj.get_gene_positions()
            g_info.insert(0, gene_obj.get_gene_name())
            genes.append(g_info)
        annot_data["genes"] = genes
        annot_data["heading"] = HEADING_FOR_ANNOTATION_GENE
    return annot_data


def get_annotation_obj_from_id(annot_id):
    """Return the instace object from the id"""
    if OrganismAnnotation.objects.filter(pk__exact=annot_id).exists():
        return OrganismAnnotation.objects.filter(pk__exact=annot_id).last()
    return None


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
    f_data["organism_code"] = seq_reg[1].split(".")[0]
    f_data["organism_code_version"] = seq_reg[1].split(".")[-1]
    if check_if_organism_version_exists(
        f_data["organism_code"], f_data["organism_code_version"]
    ):
        return {"ERROR": ERROR_ANNOTATION_ORGANISM_ALREADY_EXISTS}
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
    organism = gff_parsed["organism_code"] + "." + gff_parsed["organism_code_version"]
    if not Chromosome.objects.filter(chromosome__iexact=organism).exists():
        chromosome_obj = Chromosome.objects.create_new_chromosome(organism)
    else:
        chromosome_obj = Chromosome.objects.filter(chromosome__iexact=organism)
    gff_parsed["user"] = user
    gff_parsed["chromosomeID"] = chromosome_obj
    OrganismAnnotation.objects.create_new_annotation(gff_parsed)

    for gene in gff_parsed["genes"]:
        gene["user"] = user
        gene["chromosomeID"] = chromosome_obj
        Gene.objects.create_new_gene(gene)
    return
