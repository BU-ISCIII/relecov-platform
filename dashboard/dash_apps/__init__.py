from .heatmap_lineage import register as register_heatmap_lineage
from .mutation_table import register as register_mutation_table
from .needle_lineage import register as register_needle_lineage
from .variation_lineage import register as register_variation_lineage

_REGISTERED = False


def register_all():
    global _REGISTERED
    if _REGISTERED:
        return
    register_heatmap_lineage()
    register_mutation_table()
    register_needle_lineage()
    register_variation_lineage()
    _REGISTERED = True
