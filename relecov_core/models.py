from django.db import models


class Caller(models.Model):
    name = models.CharField(max_length=60)
    version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Caller"
        
        
        
class Prueba():
    var = 1
    dict = {"apple":"red", "onion":"white", }

"""
class Laboratory(models.Model):
    name = models.CharField(max_length=70)
    location =models.Charfield(max_length= 120)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Laboratory"
    
class Filter(models.Model):
    result = models.Charfield(max_length=70)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Filter"
    
class Effect(models.Model):
    type_of_effect = models.CharField(max_length=80)
    comments = models.Charfield(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Caller"

class Lineage(models.Model):
    scientific_name = models.CharField(max_length=100)
    common_name = models.CharField(max_length=100)
    rna_structure = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Caller"

class Gene(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Caller"

class Chrom(models.Model):
    name_ref = models.CharField(max_length=110)
    rna_structure = models.CharField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Caller"

class Sample(models.Model):
    fk_lab = models.OneToOneField(
                    Laboratory,
                    on_delete=models.CASCADE)
    reference = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Caller"

class SampleResult(models.Model):
    pos = models.CharField(max_length=7)
    ref = models.CharField(max_length=12)
    ALT = models.CharField(max_length=5)
    DP = models.CharField(max_length=7)
"""