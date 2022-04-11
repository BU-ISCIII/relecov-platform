from webbrowser import Chrome
from django.db import models

#Caller Table
class CallerManager(models.Manager):
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

#Filter Table
class FilterManager(models.Manager):
    def create_new_filter(self,data):
        new_filter = self.create(filter=data["filter"])
        return new_filter
        
        
class Filter(models.Model):
    filter = models.CharField(max_length=70)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    class Meta:
        db_table = "Filter"
        
    def __str__(self):
        return "%s" % (self.filter)
    
    objects = FilterManager()
    
#Effect Table    
class EffectManager(models.Manager):
    def create_new_effect(self, data):
        new_effect = self.create(effect=data["effect"], hgvs_c=data["hgvs_c"], hgvs_p=data["hgvs_p"], hgvs_p_1_letter=data["hgvs_p_1_letter"])
        return new_effect
    
    
class Effect(models.Model):
    effect = models.CharField(max_length=80)
    hgvs_c = models.CharField(max_length=60)
    hgvs_p = models.CharField(max_length=60)
    hgvs_p_1_letter = models.CharField(max_length=60)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "Effect"
    
    def __str__(self):
        return "%s" % (self.effect)
    
    def get_hgvs_c(self):
        return "%s" % (self.hgvs_c)

    def get_hgvs_p(self):
        return "%s" % (self.hgvs_p)
    
    def get_hgvs_p_1_letter(self):
        return "%s" % (self.hgvs_p_1_letter)
    
    objects = EffectManager()
        
#Lineage Table
class LineageManager(models.Manager):
    def create_new_Lineage(self,data):
        new_lineage = self.create(lineage=data["lineage"], week=data["week"])
        return new_lineage
    

class Lineage(models.Model):
    lineage = models.CharField(max_length=100)
    week = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "Lineage"
        
    def __str__(self):
        return "%s" % (self.lineage)
    
    def get_week(self):
        return "%s" % (self.week)
    
    objects = LineageManager()
    
#Gene Table    
class GeneManager(models.Manager):
    def create_new_gene(self, data):
        new_gene = self.create(gene=data["gene"])
        return new_gene
    
    
class Gene(models.Model):
    gene = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "Gene"
        
    def __str__(self):
        return "%s" % (self.gene)
    
    objects = GeneManager()
    
#Chromosome Table     
class ChromosomeManager(models.Manager):
    def create_new_chromosome(self, data):
        new_chomosome = self.create(chromosome=data["chromosome"])
        return new_chomosome 
    
    
class Chromosome(models.Model):
    chromosome = models.CharField(max_length=110)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "Chromosome"   
        
    def __str__(self):
        return "%s" % (self.chromosome)
    
    objects = ChromosomeManager()
    

#Sample Table         
class SampleManager(models.Manager):
    def create_new_sample(self, data):
        new_sample = self.create(sample=data["sample"])
        return new_sample


class Sample(models.Model):
    sample = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=("created at"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=("updated at"))
    
    class Meta:
        db_table = "Sample"
        
    def __str__(self):
        return "%s" % (self.sample)
    
    objects = SampleManager()
    

#Variant Table         
class VariantManager(models.Manager):
    def create_new_variant(self, data):
        new_variant = self.create(
            pos=data["pos"],
            ref=data["ref"],
            alt=data["alt"],
            dp=data["dp"],
            alt_dp=data["alt_dp"],
            ref_dp=data["ref_dp"],
            af=data["af"]
            )
        return new_variant
    
    
class Variant(models.Model): #include Foreign Keys
    """
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)
    effect = models.ForeignKey(Effect, on_delete=models.CASCADE)
    caller = models.ForeignKey(Caller, on_delete=models.CASCADE)
    filter = models.ForeignKey(Filter, on_delete=models.CASCADE)
    lineage = models.ForeignKey(Lineage, on_delete=models.CASCADE)
    chromosome = models.ForeignKey(Chromosome, on_delete=models.CASCADE)
    """
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

    def __str__(self):
        return "%s" % (self.variant)
    
    def get_pos(self):
        return "%s" % (self.pos)
    
    def get_ref(self):
        return "%s" % (self.ref)
    
    def get_alt(self):
        return "%s" % (self.alt)
    
    def get_dp(self):
        return "%s" % (self.dp)
    
    def get_alt_dp(self):
        return "%s" % (self.alt_dp)
    
    def get_ref_dp(self):
        return "%s" % (self.ref_dp)
    
    def get_af(self):
        return "%s" % (self.af)
    
    objects = VariantManager()
