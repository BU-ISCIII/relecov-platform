# Generic imports
from collections import defaultdict
from django.db.models import F
from openpyxl import Workbook

# Local imports
import core.models
import core.config
import core.utils.samples
import core.utils.plotly_graphics


def get_all_chromosome_objs():
    """Get the instance of all defined chromosomes"""
    if core.models.Chromosome.objects.all().exists():
        return core.models.Chromosome.objects.all()
    return None


def get_all_organism_objs():
    """Get the instances of all defined organism"""
    if core.models.OrganismAnnotation.objects.all().exists():
        return core.models.OrganismAnnotation.objects.all()
    return None


def get_default_chromosome():
    """Get the first defined chromosome in database as the default value.
    None is returned if no Chromosome is defined in database
    """
    if core.models.Chromosome.objects.all().exists():
        return core.models.Chromosome.objects.order_by("created_at").first()
    else:
        return None


def get_sample_in_variant_list(chromosome_obj):
    """Get all samples defined in variant in sample for the requested
    instance chromosome
    """
    v_in_sample = []
    if core.models.VariantInSample.objects.filter(
        variantID_id__chromosomeID_id=chromosome_obj
    ).exists():
        v_in_sample_objs = core.models.VariantInSample.objects.filter(
            variantID_id__chromosomeID_id=chromosome_obj
        ).order_by("-sampleID_id")
        for v_in_sample_obj in v_in_sample_objs:
            v_in_sample.append(v_in_sample_obj.get_sample_unique_id())
    return v_in_sample


def get_variant_data_from_sample(sample_id):
    """Collect the variant information for the sample"""
    data = {}
    sample_obj = core.utils.samples.get_sample_obj_from_id(sample_id)
    if sample_obj is None:
        return data
    variant_data = []
    if core.models.VariantInSample.objects.filter(sampleID_id=sample_obj).exists():
        data["heading"] = core.config.HEADING_FOR_VARIANT_TABLE_DISPLAY
        v_in_s_objs = core.models.VariantInSample.objects.filter(sampleID_id=sample_obj)
        for v_in_s_obj in v_in_s_objs:
            # DP,REF_DP,ALT_DP,AF
            v_in_s_data = v_in_s_obj.get_variant_in_sample_data()
            v_obj = v_in_s_obj.get_variantID_obj()
            # CHROM,POS,REF,ALT,FILTER
            v_data = v_obj.get_variant_data()
            v_ann_objs = core.models.VariantAnnotation.objects.filter(
                variantID_id=v_obj
            )
            if len(v_ann_objs) > 1:
                v_ann_data_p = []
                for v_ann_obj in v_ann_objs:
                    # GENE_ID, HGVS_C, HGVS_P, HGVS_P_1LETTER
                    v_ann_data_p.append(
                        [v_ann_obj.get_geneID_id()] + v_ann_obj.get_variant_annot_data()
                    )
                v_ann_data = []

                for idx in range(len(v_ann_data_p[0])):
                    if v_ann_data_p[0][idx] == v_ann_data_p[1][idx]:
                        v_ann_data.append(v_ann_data_p[0][idx])
                    else:
                        v_ann_data.append(
                            str(v_ann_data_p[0][idx] + " - " + v_ann_data_p[1][idx])
                        )
                v_ann_data_p = v_ann_data
            elif len(v_ann_objs) == 1:
                v_ann_data_p = [v_ann_objs[0].get_geneID_id()] + v_ann_objs[
                    0
                ].get_variant_annot_data()
            # Set dummy values if not variant annotation objects exists
            else:
                v_ann_data_p = ["-", "-", "-", "-"]

            variant_data.append(v_data + v_in_s_data + v_ann_data_p)
    data["variant_data"] = variant_data
    return data


VARIANTS_LONG_TABLE_COLUMNS = [
    "sample",
    "chrom",
    "pos",
    "ref",
    "alt",
    "dp",
    "ref_dp",
    "alt_dp",
    "af",
    "Gene ID",
    "hgvs_c",
    "hgvs_p",
    "hgvs_p_1_letter",
]


def merge_variant_annotation_values(annotation_values):
    """Merge annotation values following the SampleDisplay table style."""
    if not annotation_values:
        return ["-", "-", "-", "-"]
    merged_values = []
    for idx in range(len(annotation_values[0])):
        column_values = [values[idx] for values in annotation_values]
        unique_values = []
        for value in column_values:
            if value not in unique_values:
                unique_values.append(value)
        merged_values.append(" - ".join(unique_values))
    return merged_values


def get_variant_annotation_row(variant_obj, annotation_map=None):
    """Return one merged annotation row fragment for one variant."""
    if annotation_map is None:
        variant_annotations = core.models.VariantAnnotation.objects.filter(
            variantID_id=variant_obj
        ).select_related("geneID_id")
        annotations = list(variant_annotations)
    else:
        annotations = annotation_map.get(variant_obj.pk, [])
    annotation_values = [
        [
            variant_annotation.get_geneID_id(),
            variant_annotation.hgvs_c,
            variant_annotation.hgvs_p,
            variant_annotation.hgvs_p_1_letter,
        ]
        for variant_annotation in annotations
    ]
    return merge_variant_annotation_values(annotation_values)


def get_variant_annotation_map(variant_ids):
    """Return variant annotations grouped by variant ID."""
    annotation_map = defaultdict(list)
    variant_annotations = core.models.VariantAnnotation.objects.filter(
        variantID_id__in=variant_ids
    ).select_related("geneID_id")
    for variant_annotation in variant_annotations:
        annotation_map[variant_annotation.variantID_id_id].append(variant_annotation)
    return annotation_map


VARIANTS_LONG_TABLE_SAMPLE_BATCH_SIZE = 500


def _get_sequencing_id_sort_key(sequencing_id):
    """Sort like MySQL does on sequencing_sample_id: NULLs first, ignoring case."""
    return (sequencing_id is not None, (sequencing_id or "").lower())


def iter_variants_long_table_rows(filtered_rows):
    """Yield one row per sample variant annotation for filtered sample rows.

    Samples are processed in small batches and sorted in Python, so the
    database never has to join and sort the variants of every filtered sample
    in one query (which can exhaust MySQL's temporary disk space).
    """
    sample_pks = list(dict.fromkeys(row["id"] for row in filtered_rows))
    sequencing_ids = dict(
        core.models.Sample.objects.filter(pk__in=sample_pks).values_list(
            "pk", "sequencing_sample_id"
        )
    )
    sample_pks = sorted(
        sequencing_ids,
        key=lambda sample_pk: _get_sequencing_id_sort_key(sequencing_ids[sample_pk]),
    )
    for start in range(0, len(sample_pks), VARIANTS_LONG_TABLE_SAMPLE_BATCH_SIZE):
        batch_pks = sample_pks[start : start + VARIANTS_LONG_TABLE_SAMPLE_BATCH_SIZE]
        variants_by_sample = defaultdict(dict)
        for variant_in_sample in core.models.VariantInSample.objects.filter(
            sampleID_id__in=batch_pks, variantID_id__isnull=False
        ).select_related("variantID_id", "variantID_id__chromosomeID_id"):
            # Keep the first row seen for each sample and variant pair.
            variants_by_sample[variant_in_sample.sampleID_id_id].setdefault(
                variant_in_sample.variantID_id_id, variant_in_sample
            )
        annotation_map = get_variant_annotation_map(
            {
                variant_id
                for sample_variants in variants_by_sample.values()
                for variant_id in sample_variants
            }
        )
        for sample_pk in batch_pks:
            sample_variants = sorted(
                variants_by_sample.get(sample_pk, {}).values(),
                key=lambda variant_in_sample: (
                    variant_in_sample.variantID_id.pos is not None,
                    variant_in_sample.variantID_id.pos or "",
                ),
            )
            for variant_in_sample in sample_variants:
                variant_obj = variant_in_sample.variantID_id
                chromosome_obj = variant_obj.chromosomeID_id
                variant_prefix = [
                    "%s" % (sequencing_ids[sample_pk]),
                    chromosome_obj.get_chromosome_name() if chromosome_obj else "",
                    variant_obj.get_pos(),
                    variant_obj.get_ref(),
                    variant_obj.get_alt(),
                    variant_in_sample.get_dp(),
                    variant_in_sample.get_ref_dp(),
                    variant_in_sample.get_alt_dp(),
                    variant_in_sample.get_af(),
                ]
                annotation_row = get_variant_annotation_row(
                    variant_obj, annotation_map=annotation_map
                )
                yield variant_prefix + annotation_row


def get_variants_long_table_rows(filtered_rows):
    """Return one row per sample variant annotation for filtered sample rows."""
    return list(iter_variants_long_table_rows(filtered_rows))


def build_variants_long_table_workbook(filtered_rows):
    """Build the variants long table workbook for filtered sample browser rows."""
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "variants_long_table"
    worksheet.append(VARIANTS_LONG_TABLE_COLUMNS)
    for row in get_variants_long_table_rows(filtered_rows):
        worksheet.append(row)
    return workbook


def get_variant_graphic_from_sample(sample_id):
    """Collect the variant information to send to create the plotly graphic"""
    v_data = {"x": [], "y": [], "v_id": []}
    sample_obj = core.utils.samples.get_sample_obj_from_id(sample_id)
    if core.models.VariantInSample.objects.filter(sampleID_id=sample_obj).exists():
        raw_data = core.models.VariantInSample.objects.filter(
            sampleID_id=sample_obj
        ).values(x=F("variantID_id__pos"), y=F("af"), v_id=F("variantID_id__pk"))
        for r_data in raw_data:
            for key, value in r_data.items():
                v_data[key].append(value)

        v_data["mutationGroups"] = list(
            core.models.VariantAnnotation.objects.filter(
                variantID_id__pk__in=v_data["v_id"]
            ).values_list("effectID_id__effect", flat=True)
        )
        try:
            chromosome_obj = (
                core.models.VariantAnnotation.objects.filter(
                    variantID_id__pk=v_data["v_id"][0]
                )
                .last()
                .variantID_id.chromosomeID_id
            )
        except AttributeError:
            # get the chromosome obj from the second variant annotation
            chromosome_obj = (
                core.models.VariantAnnotation.objects.filter(
                    variantID_id__pk=v_data["v_id"][1]
                )
                .last()
                .variantID_id.chromosomeID_id
            )
        v_data["domains"] = get_domains_and_coordenates(chromosome_obj)
        # delete no longer needed ids
        v_data.pop("v_id")

    return core.utils.plotly_graphics.build_sample_variant_initial_arguments(v_data)


def get_gene_obj_from_gene_name(gene_name):
    if core.models.Gene.objects.filter(gene_name__iexact=gene_name).exists():
        return core.models.Gene.objects.filter(gene_name__iexact=gene_name).last()
    return None


def get_gene_list(chromosome_obj):
    """Get the list of genes defined for the requested chromosome"""
    gene_list = []
    if core.models.Gene.objects.filter(chromosomeID=chromosome_obj).exists():
        gene_objs = core.models.Gene.objects.filter(chromosomeID=chromosome_obj)
        for gene_obj in gene_objs:
            gene_list.append(gene_obj.get_gene_name())
    return gene_list


def get_domains_and_coordenates(chromosome_obj):
    """Get the coordenates and the gene names for the given chromosome"""
    domains = []
    if core.models.Gene.objects.filter(chromosomeID=chromosome_obj).exists():
        gene_objs = core.models.Gene.objects.filter(chromosomeID=chromosome_obj)
        for gene_obj in gene_objs:
            domains.append(
                {
                    "name": gene_obj.get_gene_name(),
                    "coord": "-".join(gene_obj.get_gene_positions()),
                }
            )
    return domains


"""
Functions to get data from database and paint variant mutation in
lineages needle plot graph
"""


def get_if_organism_exists(organism_code):
    if core.models.OrganismAnnotation.objects.filter(
        organism_code=organism_code
    ).exists():
        organism_obj = core.models.OrganismAnnotation.objects.filter(
            organism_code=organism_code
        ).last()
        return organism_obj
    else:
        return None
        # return {"ERROR":ERROR_CHROMOSOME_DOES_NOT_EXIST}


def get_if_chromosomes_exists(chromosome):
    if core.models.Chromosome.objects.filter(chromosome=chromosome).exists():
        chromosome_obj = core.models.Chromosome.objects.filter(
            chromosome=chromosome
        ).last()
        return chromosome_obj
    else:
        return None


def get_gene_objs(chromosome):
    """Get gene objs defined for the chromosome"""
    chromosome_obj = core.models.Chromosome.objects.filter(chromosome=chromosome).last()

    if core.models.Gene.objects.filter(chromosomeID=chromosome_obj).exists():
        return core.models.Gene.objects.filter(chromosomeID=chromosome_obj)
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
        sample_obj = core.utils.samples.get_sample_obj_from_sample_name(sample_name)
        if sample_obj:
            variant_in_sample_objs = core.models.VariantInSample.objects.filter(
                sampleID_id=sample_obj
            )
            for variant_in_sample_obj in variant_in_sample_objs:
                list_of_af.append(variant_in_sample_obj.get_af())
            return list_of_af


def create_effect_list(sample_name, chromosome):
    list_of_effects = []
    chrom_obj = get_if_chromosomes_exists(chromosome)
    if chrom_obj:
        sample_obj = core.utils.samples.get_sample_obj_from_sample_name(sample_name)
        if sample_obj:
            variant_in_sample_objs = core.models.VariantInSample.objects.filter(
                sampleID_id=sample_obj
            )
            for variant_in_sample_obj in variant_in_sample_objs:
                variant_obj = variant_in_sample_obj.get_variantID_id()
                variant_annotation_objs = core.models.VariantAnnotation.objects.filter(
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
        sample_obj = core.utils.samples.get_sample_obj_from_sample_name(sample_name)
        if sample_obj:
            variant_in_sample_objs = core.models.VariantInSample.objects.filter(
                sampleID_id=sample_obj
            )
            for variant_in_sample_obj in variant_in_sample_objs:
                list_of_position.append(variant_in_sample_obj.get_variant_pos())
            return list_of_position
