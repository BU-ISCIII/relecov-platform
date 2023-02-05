from django.db.models import F

from relecov_core.models import (
    VariantAnnotation,
    VariantInSample,
    Chromosome,
    Gene,
    OrganismAnnotation,
)

from relecov_core.utils.handling_samples import (
    get_sample_obj_from_id,
    get_sample_obj_from_sample_name,
)

from relecov_core.core_config import HEADING_FOR_VARIANT_TABLE_DISPLAY


from relecov_core.utils.plotly_graphics import needle_plot


def get_all_chromosome_objs():
    """Get the instance of all defined chromosomes"""
    if Chromosome.objects.all().exists():
        return Chromosome.objects.all()
    return None


def get_all_organism_objs():
    """Get the instances of all defined organism"""
    if OrganismAnnotation.objects.all().exists():
        return OrganismAnnotation.objects.all()
    return None


def get_default_chromosome():
    """Get the first defined chromosome in database as the default value.
    None is returned if no Chromosome is defined in database
    """
    if Chromosome.objects.all().exists():
        return Chromosome.objects.order_by("created_at").first()
    else:
        return None


def get_sample_in_variant_list(chromosome_obj):
    """Get all samples defined in variant in sample for the requested
    instance chromosome
    """
    v_in_sample = []
    if VariantInSample.objects.filter(
        variantID_id__chromosomeID_id=chromosome_obj
    ).exists():
        v_in_sample_objs = VariantInSample.objects.filter(
            variantID_id__chromosomeID_id=chromosome_obj
        ).order_by("-sampleID_id")
        for v_in_sample_obj in v_in_sample_objs:
            v_in_sample.append(v_in_sample_obj.get_sample_name())
    return v_in_sample


def get_variant_data_from_sample(sample_id):
    """Collect the variant information for the sample"""
    data = {}
    sample_obj = get_sample_obj_from_id(sample_id)
    if sample_obj is None:
        return data
    variant_data = []
    if VariantInSample.objects.filter(sampleID_id=sample_obj).exists():
        data["heading"] = HEADING_FOR_VARIANT_TABLE_DISPLAY
        v_in_s_objs = VariantInSample.objects.filter(sampleID_id=sample_obj)
        for v_in_s_obj in v_in_s_objs:
            # DP,REF_DP,ALT_DP,AF
            v_in_s_data = v_in_s_obj.get_variant_in_sample_data()
            v_obj = v_in_s_obj.get_variantID_obj()
            # CHROM,POS,REF,ALT,FILTER
            v_data = v_obj.get_variant_data()
            v_ann_objs = VariantAnnotation.objects.filter(variantID_id=v_obj)
            if len(v_ann_objs) > 1:
                v_ann_data_p = []
                for v_ann_obj in v_ann_objs:
                    # HGVS_C	HGVS_P	HGVS_P_1LETTER
                    v_ann_data_p.append(v_ann_obj.get_variant_annot_data())
                v_ann_data = []

                for idx in range(len(v_ann_data_p[0])):
                    if v_ann_data_p[0][idx] == v_ann_data_p[1][idx]:
                        v_ann_data.append(v_ann_data_p[0][idx])
                    else:
                        v_ann_data.append(
                            str(v_ann_data_p[0][idx] + " - " + v_ann_data_p[1][idx])
                        )
                v_ann_data_p = v_ann_data
            else:
                v_ann_data_p = v_ann_objs[0].get_variant_annot_data()

            variant_data.append(v_data + v_in_s_data + v_ann_data_p)
    data["variant_data"] = variant_data
    return data


def get_variant_graphic_from_sample(sample_id):
    """Collect the variant information to send to create the plotly graphic"""
    v_data = {"x": [], "y": [], "v_id": []}
    sample_obj = get_sample_obj_from_id(sample_id)
    if VariantInSample.objects.filter(sampleID_id=sample_obj).exists():
        raw_data = VariantInSample.objects.filter(sampleID_id=sample_obj).values(
            x=F("variantID_id__pos"), y=F("af"), v_id=F("variantID_id__pk")
        )
        for r_data in raw_data:
            for key, value in r_data.items():
                v_data[key].append(value)

        v_data["mutationGroups"] = list(
            VariantAnnotation.objects.filter(
                variantID_id__pk__in=v_data["v_id"]
            ).values_list("effectID_id__effect", flat=True)
        )
        chromosome_obj = (
            VariantAnnotation.objects.filter(variantID_id__pk=v_data["v_id"][0])
            .last()
            .variantID_id.chromosomeID_id
        )
        v_data["domains"] = get_domains_and_coordenates(chromosome_obj)
        # delete no longer needed ids
        v_data.pop("v_id")

    return needle_plot(v_data)


def get_gene_obj_from_gene_name(gene_name):
    if Gene.objects.filter(gene_name__iexact=gene_name).exists():
        return Gene.objects.filter(gene_name__iexact=gene_name).last()
    return None


def get_gene_list(chromosome_obj):
    """Get the list of genes defined for the requested chromosome"""
    gene_list = []
    if Gene.objects.filter(chromosomeID=chromosome_obj).exists():
        gene_objs = Gene.objects.filter(chromosomeID=chromosome_obj)
        for gene_obj in gene_objs:
            gene_list.append(gene_obj.get_gene_name())
    return gene_list


def get_domains_and_coordenates(chromosome_obj):
    """Get the coordenates and the gene names for the given chromosome"""
    domains = []
    if Gene.objects.filter(chromosomeID=chromosome_obj).exists():
        gene_objs = Gene.objects.filter(chromosomeID=chromosome_obj)
        for gene_obj in gene_objs:
            domains.append(
                {
                    "name": gene_obj.get_gene_name(),
                    "coord": "-".join(gene_obj.get_gene_positions()),
                }
            )
    return domains


"""
<<<<<<< HEAD
Functions to get data from database and paint variant mutation in
=======
Functions to get data from database and paint variant mutation in 
>>>>>>> solving litin
lineages needle plot graph
"""


def get_if_organism_exists(organism_code):
    if OrganismAnnotation.objects.filter(organism_code=organism_code).exists():
        organism_obj = OrganismAnnotation.objects.filter(
            organism_code=organism_code
        ).last()
        return organism_obj
    else:
        return None
        # return {"ERROR":ERROR_CHROMOSOME_DOES_NOT_EXIST}


def get_if_chromosomes_exists(chromosome):
    if Chromosome.objects.filter(chromosome=chromosome).exists():
        chromosome_obj = Chromosome.objects.filter(chromosome=chromosome).last()
        return chromosome_obj
    else:
        return None


def get_gene_objs(chromosome):
    """Get gene objs defined for the chromosome"""
    chromosome_obj = Chromosome.objects.filter(chromosome=chromosome).last()

    if Gene.objects.filter(chromosomeID=chromosome_obj).exists():
        return Gene.objects.filter(chromosomeID=chromosome_obj)
    return None


def get_domains_list(chromosome):
    domains = []
    gene_objs = get_gene_objs(chromosome)
    for gene_obj in gene_objs:
        gene_data = {}
        coords = "-".join(gene_obj.get_gene_positions())
        gene_data = {"name": gene_obj.get_gene_name(), "coord": coords}
        domains.append(gene_data)

    return domains


def get_alelle_frequency_per_sample(sample_name, chromosome):
    list_of_af = []
    chrom_obj = get_if_chromosomes_exists(chromosome)
    if chrom_obj:
        sample_obj = get_sample_obj_from_sample_name(sample_name)
        if sample_obj:
            variant_in_sample_objs = VariantInSample.objects.filter(
                sampleID_id=sample_obj
            )
            for variant_in_sample_obj in variant_in_sample_objs:
                list_of_af.append(variant_in_sample_obj.get_af())
            return list_of_af


def create_effect_list(sample_name, chromosome):
    list_of_effects = []
    chrom_obj = get_if_chromosomes_exists(chromosome)
    if chrom_obj:
        sample_obj = get_sample_obj_from_sample_name(sample_name)
        if sample_obj:
            variant_in_sample_objs = VariantInSample.objects.filter(
                sampleID_id=sample_obj
            )
            for variant_in_sample_obj in variant_in_sample_objs:
                variant_obj = variant_in_sample_obj.get_variantID_id()
                variant_annotation_objs = VariantAnnotation.objects.filter(
                    variantID_id=variant_obj
                )

                for variant_annotation_obj in variant_annotation_objs:
                    list_of_effects.append(
                        variant_annotation_obj.get_variant_annot_data()[1]
                    )
                    break
    return list_of_effects


def get_position_per_sample(sample_name, chromosome):
    list_of_position = []
    chrom_obj = get_if_chromosomes_exists(chromosome)
    if chrom_obj:
        sample_obj = get_sample_obj_from_sample_name(sample_name)
        if sample_obj:
            variant_in_sample_objs = VariantInSample.objects.filter(
                sampleID_id=sample_obj
            )
            for variant_in_sample_obj in variant_in_sample_objs:
                list_of_position.append(variant_in_sample_obj.get_variant_pos())
            return list_of_position


def create_dataframe(sample_name, organism_code):
    mdata = {}
    """
    domains = create_domains_list_of_dict(organism_code)
    af = get_alelle_frequency_per_sample(sample_name, organism_code)
    pos = get_position_per_sample(sample_name, organism_code)
    effects = create_effect_list(sample_name, organism_code)

    mdata["x"] = pos
    mdata["y"] = af
    mdata["mutationGroups"] = effects
    mdata["domains"] = domains
    """
    return mdata
