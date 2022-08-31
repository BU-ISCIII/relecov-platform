from relecov_core.models import (
    LineageFields,
    LineageValues,
    Variant,
    VariantAnnotation,
    VariantInSample,
    Chromosome,
    Gene,
    OrganismAnnotation,
    Sample,
)


from relecov_core.utils.handling_samples import (
    get_sample_obj_from_id,
    get_sample_obj_from_sample_name,
)

"""
SAMPLE,CHROM,POS,REF,ALT,FILTER,DP,REF_DP,ALT_DP,AF,GENE,EFFECT,HGVS_C,HGVS_P,HGVS_P_1LETTER,CALLER,LINEAGE
"""


def get_variant_data_from_sample(sample_id):
    """Collect the variant information for the sample"""
    sample_obj = get_sample_obj_from_id(sample_id)
    if not sample_obj:
        return None
    variant_data = []
    if VariantInSample.objects.filter(sampleID_id=sample_obj).exists():
        v_in_s_objs = VariantInSample.objects.filter(sampleID_id=sample_obj)
        for v_in_s_obj in v_in_s_objs:
            # DP,REF_DP,ALT_DP,AF
            v_in_s_data = v_in_s_obj.get_variant_in_sample_data()
            v_objs = Variant.objects.filter(variant_in_sampleID_id=v_in_s_obj)
            for v_obj in v_objs:
                # CHROM,POS,REF,ALT,FILTER
                v_data = v_obj.get_variant_in_sample_data()
                v_ann_objs = VariantAnnotation.objects.filter(variantID_id=v_obj)
                v_ann_data_p = []
                for v_ann_obj in v_ann_objs:
                    # HGVS_C	HGVS_P	HGVS_P_1LETTER
                    v_ann_data_p.append(v_ann_obj.get_variant_in_sample_data())
                if len(v_ann_data_p) > 1:
                    v_ann_data = []
                    for idx in range(len(v_ann_data_p)):
                        if v_ann_data_p[0][idx] == v_ann_data_p[1][idx]:
                            v_ann_data.append(v_ann_data_p[0][idx])
                        else:
                            v_ann_data.append(
                                str(v_ann_data_p[0][idx] + " - " + v_ann_data_p[1][idx])
                            )
        variant_data.append([v_data + v_in_s_data + v_ann_data])
    return variant_data


def get_gene_obj_from_gene_name(gene_name):
    if Gene.objects.filter(gene_name__iexact=gene_name).exists():
        return Gene.objects.filter(gene_name__iexact=gene_name).last()
    return None


"""
Functions to get data from database and paint variant mutation in lineages needle plot graph
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


def get_gene_objs(organism_code):
    organism_obj = get_if_organism_exists(organism_code=organism_code)
    if organism_obj:
        if Gene.objects.filter(org_annotationID=organism_obj).exists():
            return Gene.objects.filter(org_annotationID=organism_obj)
    return None


def create_domains_list_of_dict(organism_code):
    separator = "-"
    dict_of_domain = {}
    domains = []
    gene_data_objs = get_gene_objs(organism_code)
    for gene_data_obj in gene_data_objs:
        list_of_coordenates = gene_data_obj.get_gene_positions()
        coords = separator.join(list_of_coordenates)
        dict_of_domain = {"name": gene_data_obj.get_gene_name(), "coord": coords}
        domains.append(dict_of_domain)

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
                        variant_annotation_obj.get_variant_in_sample_data()
                    )

        return list_of_effects


def get_position_per_sample(sample_name, chromosome):
    list_of_position = []
    list_of_effects = []
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
                    list_of_effects.append(variant_annotation_obj.get_effectID_id())

        return list_of_effects


def create_dataframe(sample, organism_code):
    mdata = {}
    domains = create_domains_list_of_dict(organism_code)
    af = get_alelle_frequency_per_sample(sample, organism_code)
    pos = get_position_per_sample(sample, organism_code)
    effects = create_effect_list(sample, organism_code)

    mdata["x"] = pos
    mdata["y"] = af
    mdata["mutationGroups"] = effects
    mdata["domains"] = domains

    return mdata


# ITER variant mutation
def get_variant_data_from_lineages(lineage, organism_code):
    # import pdb
    mdata = {}
    list_of_af = []
    list_of_pos = []
    list_of_effects = []

    domains = create_domains_list_of_dict(organism_code)

    lineage_fields_obj = LineageFields.objects.filter(
        property_name="lineage_name"
    ).last()
    lineage_value_obj = LineageValues.objects.filter(
        lineage_fieldID=lineage_fields_obj.get_lineage_field_id(), value=lineage
    ).last()
    print(lineage_value_obj)
    sample_objs = Sample.objects.filter(linage_values=lineage_value_obj)
    for sample_obj in sample_objs:
        print(sample_obj)
        af = get_alelle_frequency_per_sample(
            sample_obj.get_sequencing_sample_id(), organism_code
        )
        pos = get_position_per_sample(
            sample_obj.get_sequencing_sample_id(), organism_code
        )
        effects = create_effect_list(
            sample_obj.get_sequencing_sample_id(), organism_code
        )

        list_of_af += af
        list_of_pos += pos
        list_of_effects += effects
        # pdb.set_trace()

    mdata["x"] = list_of_pos
    mdata["y"] = list_of_af
    mdata["mutationGroups"] = list_of_effects
    mdata["domains"] = domains

    return mdata
