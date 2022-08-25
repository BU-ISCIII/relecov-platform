from relecov_core.models import (
    Variant,
    VariantAnnotation,
    VariantInSample,
)

from relecov_core.utils.handling_samples import get_sample_obj_from_id

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
