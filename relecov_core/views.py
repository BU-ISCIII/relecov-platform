from multiprocessing import context
from relecov_core.models import *
from django.shortcuts import render

def index(request):
    context = {}
    return render(request, "relecov_core/index.html", context)
def variants(request):
    context = {}
    return render(request, "relecov_core/variants.html", context)

def documentation(request):
    context = {}
    return render(request, "relecov_core/documentation.html", context)

def readTest(request):
    data_array = []#one field per position
    variant_dict = {}
    variant_list = []
    effect_dict = {}
    effect_list = []
    filter_dict = {}
    filter_list = []
    chromosome_dict = {}
    chromosome_list = []
    sample_dict = {}
    sample_list = []
    caller_dict = {}
    caller_list = []
    lineage_dict = {}
    lineage_list = []
    gene_dict = {}
    gene_list = []
    
    #fields => SAMPLE(0), CHROM(1), POS(2), REF(3), ALT(4), FILTER(5), DP(6),  REF_DP(7), ALT_DP(8), AF(9), GENE(10), EFFECT(11), HGVS_C(12), 
    #   HGVS_P(13), HGVS_P1LETTER(14), CALLER(15), LINEAGE(16)
    with open("relecov_core/docs/variants1.csv") as fh:
        lines = fh.readlines()
    for line in lines[1:]:
        data_array = line.split(",")
        #variant_dict
        variant_dict["pos"] =data_array[2]
        variant_dict["ref"] =data_array[3]
        variant_dict["alt"] =data_array[4]
        variant_dict["dp"] =data_array[6]
        variant_dict["ref_dp"] =data_array[7]
        variant_dict["alt_dp"] =data_array[8]
        variant_dict["af"] =data_array[9]
        variant_dict_copy = variant_dict.copy()
        
        variant_list.append(variant_dict_copy)
        #effect _dict
        effect_dict["effect"] = data_array[11]
        effect_dict["hgvs_c"] = data_array[12]
        effect_dict["hgvs_p"] = data_array[13]
        effect_dict["hgvs_p_1_letter"] = data_array[14]
        effect_dict_copy = effect_dict.copy()
        effect_list.append(effect_dict_copy)
        #filter
        filter_dict["filter"] = data_array[5]
        filter_dict_copy = filter_dict.copy()
        filter_list.append(filter_dict_copy)
        #chromosome
        chromosome_dict["chromosome"] = data_array[1]
        chromosome_dict_copy = chromosome_dict.copy()
        chromosome_list.append(chromosome_dict_copy)
        #sample
        sample_dict["sample"] = data_array[0]
        sample_dict_copy = sample_dict.copy()
        sample_list.append(sample_dict_copy)
        #caller
        caller_dict["caller"] = data_array[15]
        caller_dict_copy = caller_dict.copy()
        caller_list.append(caller_dict_copy)
        #lineage
        lineage_dict["lineage"] = data_array[16]
        lineage_dict_copy = lineage_dict.copy()
        lineage_list.append(lineage_dict_copy)
        #gene
        gene_dict["gene"] = data_array[10]
        gene_dict_copy = gene_dict.copy()
        gene_list.append(gene_dict_copy)
      
    #insert into mySQL database
    for caller in caller_list:
        callers = Caller(caller=caller["caller"])
        callers.save()
    
    for variant in variant_list:
        variants = Variant(
            pos=variant["pos"],
            ref=variant["ref"],
            alt = variant["alt"],
            dp = variant["dp"],
            ref_dp = variant["ref_dp"],
            alt_dp = variant["alt_dp"],
            af = variant["af"],
            )
        variants.save()
    
    for effect in effect_list:
        effects = Effect(
            effect = effect["effect"],
            hgvs_c = effect["hgvs_c"],
            hgvs_p = effect["hgvs_p"],
            hgvs_p_1_letter = effect["hgvs_p_1_letter"],
        )
        effects.save()

    for filter in filter_list:
        filters = Filter(
            filter = filter["filter"]
        )
        filters.save()
        
    for chrom in chromosome_list:
        chroms = Chromosome(
            chromosome = chrom["chromosome"]
        )
        chroms.save()
        
    for samp in sample_list:
        samples = Sample(
            sample = samp["sample"]
        )
        samples.save()
        
    for lineag in lineage_list:
        lineages = Lineage(
            lineage = lineag["lineage"]
        )
        lineages.save()
        
    for gen in gene_list:
        genes = Gene(
            gene = gen["gene"]
        )
        genes.save()
    
    """
    #Delete all register into tables 
    variants = Variant.objects.all()
    variants.delete()
    
    effects = Effect.objects.all()
    effects.delete()
    
    filters = Filter.objects.all()
    filters.delete()
    
    chromosomes = Chromosome.objects.all()
    chromosomes.delete()
    
    samples = Sample.objects.all()
    samples.delete()
    
    callers = Caller.objects.all()
    callers.delete()
    
    lineages = Lineage.objects.all()
    lineages.delete()
    
    genes = Gene.objects.all()
    genes.delete()
    """
    #Context    
    context = {
        "variant":variant_list, 
        "chromosome":chromosome_list,
        "effect":effect_list,
        "sample":sample_list,
        "filter":filter_list,
        "caller":caller_list,
        "lineage":lineage_list,
        "gene":gene_list,
        }      
    
    return render(request, "relecov_core/documentation.html", context)  

