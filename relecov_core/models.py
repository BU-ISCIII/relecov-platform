from django.db import models


class CallerManager(models.Model):
    def create_new_caller(self, data):
        new_caller = self.create(name=data["name"], version=data['version'])
        return new_caller


class Caller(models.Model):
    name = models.CharField(max_length=60)
    version = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))

    class Meta:
        db_table = "Caller"

    def __str__(self):
        return "%s" % (self.name)

    objects = CallerManager()


class Prueba():
    var = 1
    dict = {"apple": "red", "onion": "white", }


"""
class Laboratory(models.Model):
    name = models.CharField(max_length=70)
    location =models.Charfield(max_length= 120)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=('created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=('updated at'))
    class Meta:
        db_table = "Laboratory"


class Filter(models.Model):
    filter = models.CharField(max_length=70)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    class Meta:
        db_table = "Filter"

class Effect(models.Model):
    effect = models.CharField(max_length=80)
    hgvs_c = models.CharField(max_length=60)
    hgvs_p = models.CharField(max_length=60)
    hgvs_p_1_letter = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    class Meta:
        db_table = "Effect"

class Lineage(models.Model):
    lineage = models.CharField(max_length=100)
    week = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    class Meta:
        db_table = "Lineage"

class Gene(models.Model):
    gene = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "Gene"

class Chromosome(models.Model):
    chromosome = models.CharField(max_length=110)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "Chromosome"

class Sample(models.Model):
    sample = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "Sample"

class Variant(models.Model): #include Foreign Keys
    pos = models.CharField(max_length=7)
    ref = models.CharField(max_length=60)
    alt = models.CharField(max_length=10)
    dp = models.CharField(max_length=10)
    alt_dp = models.CharField(max_length=5)
    ref_dp = models.CharField(max_length=10)
    af = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "Variant"
"""
