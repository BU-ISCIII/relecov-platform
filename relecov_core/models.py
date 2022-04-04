from django.db import models


class Caller(models.Model):
    caller = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Caller"
        
          
class Filter(models.Model):
    filter = models.CharField(max_length=70)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Filter"
    
class Effect(models.Model):
    effect = models.CharField(max_length=80)
    hgvs_c = models.CharField(max_length=60)
    hgvs_p = models.CharField(max_length=60)
    hgvs_p_1_letter = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Effect"

class Lineage(models.Model):
    lineage = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Lineage"

class Gene(models.Model):
    gene = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    
    class Meta:
        db_table = "Gene"

class Chromosome(models.Model):
    chromosome = models.CharField(max_length=110)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    
    class Meta:
        db_table = "Chromosome"

class Sample(models.Model):
    sample = models.CharField(max_length=50)
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
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    
    class Meta:
        db_table = "Variants"
