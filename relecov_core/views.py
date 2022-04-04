from multiprocessing import context
from relecov_core.models import Caller
from django.shortcuts import render

def index(request):
    context = {}
    return render(request, 'relecov_core/index.html', context)
def variants(request):
    context = {}
    return render(request, 'relecov_core/variants.html', context)

def documentation(request):
    context = {}
    return render(request, 'relecov_core/documentation.html', context)

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
        #fields => SAMPLE(0), CHROM(1), POS(2), REF(3), ALT(4), FILTER(5), DP(6),  REF_DP(7), ALT_DP(8), AF(9), GENE(10), EFFECT(11), HGVS_C(12), HGVS_P(13), HGVS_P1LETTER(14), CALLER(15), LINEAGE(16)
        variant_list.append(variant_dict)
        #effect _dict
        effect_dict["effect"] = data_array[11]
        effect_dict["hgvs_c"] = data_array[12]
        effect_dict["hgvs_p"] = data_array[13]
        effect_dict["hgvs_p_1_letter"] = data_array[14]
        effect_list.append(effect_dict)
        #filter
        filter_dict["filter"] = data_array[5]
        filter_list.append(filter_dict)
        #chromosome
        chromosome_dict["chromosome"] = data_array[1]
        chromosome_list.append(chromosome_dict)
        #sample
        sample_dict["sample"] = data_array[0]
        sample_list.append(sample_dict)
        #caller
        caller_dict["caller"] = data_array[15]
        caller_list.append(caller_dict)
        #lineage
        lineage_dict["lineage"] = data_array[16]
        lineage_list.append(lineage_dict)
        #gene
        gene_dict["gene"] = data_array[10]
        gene_list.append(gene_dict)
        
    #insert into mySQL database
    """
    for caller in caller_list:
                callers = Caller(name=caller)
                callers.save()
    """
    context = {"variants":variant_list,}   
    print("variant_list: " + str(variant_list))
    
    return render(request, 'relecov_core/documentation.html', context)  

    """
    def readTest(request):
        line_counter = False
    header_line = ""
    data_array = []#one field per position
    effect_list = []
    variant_list = []
    filter_list = []
    chromosome_list = []
    sample_list = []
    caller_list = []
    lineage_list = []
    gene_list = []
    
    with open("relecov_core/docs/variants1.csv") as f:

        for linea in f:
            if  not line_counter:
                header_line = linea #Header (field name)
                print("header: " + linea)
                line_counter = True
            else:
                #data_lines_list.append(linea)#rest of lines (data)
                data_array = linea.split(",")
                #fields => SAMPLE, CHROM, POS, REF, ALT, FILTER, DP,  REF_DP, ALT_DP, AF, GENE, EFFECT, HGVS_C, HGVS_P, HGVS_P1LETTER, CALLER, LINEAGE
                variant_list.append(data_array[2] + "," + data_array[3] + "," + data_array[4] + "," + data_array[6] + "," + data_array[7] + "," + data_array[8]
                                    + "," + data_array[9])
                effect_list.append(data_array[11] + "," + data_array[12] + "," + data_array[13] + "," + data_array[14])
                chromosome_list.append(data_array[1])
                sample_list.append(data_array[0])
                filter_list.append(data_array[5])
                caller_list.append(data_array[15])
                lineage_list.append(data_array[16])
                gene_list.append(data_array[10])
            
            for caller in caller_list:
                callers = Caller(name=caller, version="2.0")
                callers.save()
            
    context = {
        "variants":variant_list, 
        "chromosome":chromosome_list,
        "effect":effect_list,
        "sample":sample_list,
        "filter":filter_list,
        "caller":caller_list,
        "lineage":lineage_list,
        "gene":gene_list,
        "header":header_line,
        }   
    #print("variant_list: " + str(variant_list))
    #print("effect_list: " + str(effect_list))
    #print("chromosome_list: " + str(chromosome_list))
    #print("sample_list: " + str(sample_list))
    #print("filter_list: " + str(filter_list))
    #print("caller_list: " + str(caller_list))
    #print("lineage_list: " + lineage_list)
    #print("gene_list: " + gene_list)
    
    return render(request, 'relecov_core/documentation.html', context=context)  
    """
    
