import csv
import os
from django.conf import settings
#from msilib.schema import File
#from msilib.schema import File
#

from django.core.files import File
#from django.core.files.base import ContentFile
from django.http import HttpResponse
from django.shortcuts import render

from relecov_platform.settings import BASE_DIR



# Create your views here.
def index(request):
    context = {}
    return render(request, 'relecov_core/index.html', context)

def dashboard(request):
    context = {}
    return render(request, 'relecov_core/methodology.html', context)
    
def variants(request):
    context = {}
    return render(request, 'relecov_core/variants.html', context)

def documentation(request):
    context = {}
    return render(request, 'relecov_core/documentation.html', context)

def readTest(request):
    i = 0
    header_line = ""
    data_lines_list = []
    effect_list = []
    variant_list = []
    filter_list = []
    chromosome_list = []
    sample_list = []
    caller_list = []
    lineage_list = []
    gene_list = []
    data_array = []

    with open("relecov_core/docs/variants1.csv") as f:

        for linea in f:
            if i == 0:
                #Header, field name
                header_line = linea
                print("header: " + linea)
                i += 1
            else:
                #rest of lines
                data_lines_list.append(linea)

        print("*******************DATA******************************************")
        for data_line in data_lines_list:
            data_array.append(data_line.split(","))

        for data in data_array:
            #fields => POS, REF, ALT, DP, REF_DP, ALT_DP, AF
            variant_list.append(data[2] + "," + data[3] + "," + data[4] + "," + data[6] + "," + data[7] + "," + data[8]
                                + "," + data[9])
            effect_list.append(data[12] + "," + data[13] + "," + data[14])
            chromosome_list.append(data[1])
            sample_list.append(data[0])
            filter_list.append(data[5])
            caller_list.append(data[15])
            lineage_list.append(data[16])
            gene_list.append(data[10])

    #for caller in caller_list:
        
    #print("variant_list: " + str(variant_list))
    #print("effect_list: " + str(effect_list))
    #print("chromosome_list: " + str(chromosome_list))
    #print("sample_list: " + str(sample_list))
    #print("filter_list: " + str(filter_list))
    #print("caller_list: " + str(caller_list))
    #print("lineage_list: " + lineage_list)
    #print("gene_list: " + gene_list)
    
    return render(request, 'relecov_core/documentation.html', {"reader":lineage_list}) 