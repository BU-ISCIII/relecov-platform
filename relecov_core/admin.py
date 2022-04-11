from django.contrib import admin
from .models import *

class CallerAdmin(admin.ModelAdmin):
    list_display = ["name", "version"]


class FilterAdmin(admin.ModelAdmin):
    list_display = ["filter"]
    
    
class EffectAdmin(admin.ModelAdmin):
    list_display = ["effect", "hgvs_c", "hgvs_p", "hgvs_p_1_letter"]
    
    
class LineageAdmin(admin.ModelAdmin):
    list_display = ["lineage", "week"]
    
    
class GeneAdmin(admin.ModelAdmin):
    list_display = ["gene"]
    
    
class ChromosomeAdmin(admin.ModelAdmin):
    list_display = ["chromosome"]
    
    
class SampleAdmin(admin.ModelAdmin):
    list_display = ["sample"]
    
    
class VariantAdmin(admin.ModelAdmin):
    list_display = ["pos", "ref", "alt", "dp", "alt_dp", "ref_dp", "af"]
    

# Register models 
admin.site.register(Caller, CallerAdmin)
admin.site.register(Filter, FilterAdmin)
admin.site.register(Effect, EffectAdmin)
admin.site.register(Lineage, LineageAdmin)
admin.site.register(Gene, GeneAdmin)
admin.site.register(Chromosome, ChromosomeAdmin)
admin.site.register(Sample, SampleAdmin)
admin.site.register(Variant, VariantAdmin)