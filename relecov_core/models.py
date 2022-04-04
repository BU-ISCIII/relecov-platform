from django.db import models


class Caller(models.Model):
    name = models.CharField(max_length=60)
    version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Caller"
        
          
class Filter(models.Model):
    name = models.CharField(max_length=70)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Filter"
    
class Effect(models.Model):
    type_of_effect = models.CharField(max_length=80)
    comments = models.CharField(max_length=140)         #blob??????
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Effect"

class Lineage(models.Model):
    scientific_name = models.CharField(max_length=100)
    common_name = models.CharField(max_length=100)
    rna_structure = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Lineage"

class Gene(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    
    class Meta:
        db_table = "Gene"

class Chromosome(models.Model):
    name_ref = models.CharField(max_length=110)
    rna_structure = models.CharField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    
    class Meta:
        db_table = "Chromosome"

class Sample(models.Model):
    reference = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    
    class Meta:
        db_table = "Sample"

class variants(models.Model):
    pos = models.CharField(max_length=7)
    ref = models.CharField(max_length=12)
    alt = models.CharField(max_length=10)
    dp = models.CharField(max_length=10)
    alt_dp = models.CharField(max_length=5)
    ref_dp = models.CharField(max_length=10)
    af = models.CharField(max_length=6)
    hgvs_c = models.CharField(max_length=40)
    hgvs_p = models.CharField(max_length=40)
    hgvs_p_1_letter = models.CharField(max_length=40)
    
    class Meta:
        db_table = "Variants"
